import os
import json
import time
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from functools import wraps
from dotenv import load_dotenv
from fastapi import Body, FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.playground import Playground

# Importe suas ferramentas customizadas
from tools.suporte_tool import SuporteTool
from tools.cadastros_tool import CadastrosTool
from tools.duvidas_tool import DuvidasTool
from tools.atribui_cidade_tool import AtribuiCidadeTool
from tools.contato_categoria_tool import ContatoCategoriaTool
from tools.duckduckgo_search_tool import duckduckgo_search
from tools.knowledge_retriever_tool import retrieve_similar_documents

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# --- Configuração de Logging Estruturado ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('playground.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Configuração de Rate Limiting ---
limiter = Limiter(key_func=get_remote_address)

# --- Configuração de Cache ---
# Cache para resultados de busca e outras operações custosas
search_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutos
city_cache = TTLCache(maxsize=100, ttl=3600)     # 1 hora

# --- Configurações Externas ---
@dataclass
class AppConfig:
    """Configurações centralizadas da aplicação"""
    MAX_CONVERSATION_ID_LENGTH = 6
    MAX_CONTACT_ID_LENGTH = 10
    AGENT_STORAGE_PATH = "tmp/agents.db"
    KNOWLEDGE_BASE_FILE = "knowledge_base.md"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Carrega cidades válidas de arquivo JSON ou usa padrão
    @staticmethod
    def load_valid_cities(cities_file: str = None) -> Dict[str, str]:
        """
        Lê o arquivo JSON de cidades válidas. Se não existir ou estiver corrompido, faz fallback seguro para o padrão.
        Sempre retorna um dicionário válido e faz logging detalhado.
        Parâmetro opcional cities_file para facilitar testes.
        """
        if cities_file is None:
            cities_file = "config/cidades.json"
        default_cities = {
            "matupa": "Matupa",
            "matupá": "Matupa",
            "guaranta": "Guaranta",
            "guarantã": "Guaranta",
            "guarantã do norte": "Guaranta",
            "peixoto": "Peixoto",
            "peixoto de azevedo": "Peixoto",
            "monte verde": "Monte Verde",
            "nova monte verde": "Monte Verde",
            "bandeirantes": "Bandeirantes",
            "alta floresta": "Alta Floresta",
            "nova canaa": "Nova Canaa",
            "nova canaã": "Nova Canaa",
            "nova canaa do norte": "Nova Canaa",
            "nova canaã do norte": "Nova Canaa",
            "colider": "Colider",
            "colidér": "Colider"
        }
        try:
            if os.path.exists(cities_file):
                with open(cities_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and data:
                        logger.info(f"Cidades carregadas do arquivo {cities_file}: {list(data.values())}")
                        return data
                    else:
                        logger.warning(f"Arquivo {cities_file} está vazio ou mal formatado. Usando fallback.")
        except Exception as e:
            logger.warning(f"Não foi possível carregar cidades do arquivo {cities_file}: {e}. Usando fallback.")
        logger.info(f"Usando cidades padrão: {list(default_cities.values())}")
        return default_cities

# --- Funções de Validação Centralizadas ---
def validate_conversation_id(conversation_id: str) -> bool:
    """Valida se o conversation_id é uma string numérica de tamanho adequado."""
    if not conversation_id:
        return False
    return conversation_id.isdigit() and len(conversation_id) <= AppConfig.MAX_CONVERSATION_ID_LENGTH

def validate_contact_id(contact_id: str) -> bool:
    """Valida se o contact_id é uma string numérica válida."""
    if not contact_id or contact_id == "undefined":
        return False
    return contact_id.isdigit() and len(contact_id) <= AppConfig.MAX_CONTACT_ID_LENGTH

def validate_category(category: str) -> bool:
    """Valida se a categoria é válida."""
    valid_categories = ["Passageiro", "Motorista"]
    return category in valid_categories

# --- Decoradores para Melhorar Resiliência ---
def circuit_breaker(max_failures=3, timeout=60):
    """Implementa um circuit breaker simples"""
    failures = []
    last_failure = 0

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal failures, last_failure
            # Verifica se o circuito está aberto
            if len(failures) >= max_failures:
                time_since_last = time.time() - last_failure
                if time_since_last < timeout:
                    logger.error(f"[CIRCUIT BREAKER] Circuito aberto para {func.__name__} - aguardando {timeout - time_since_last:.1f}s")
                    raise Exception("Circuit breaker está aberto - serviço temporariamente indisponível")
                else:
                    logger.info(f"[CIRCUIT BREAKER] Timeout atingido, resetando circuito para {func.__name__}")
                    failures.clear()
            try:
                result = func(*args, **kwargs)
                if failures:
                    logger.info(f"[CIRCUIT BREAKER] Sucesso em {func.__name__}, resetando falhas")
                failures.clear()
                return result
            except Exception as e:
                failures.append(e)
                last_failure = time.time()
                logger.warning(f"[CIRCUIT BREAKER] Falha em {func.__name__}: {e} ({len(failures)}/{max_failures})")
                raise
        return wrapper
    return decorator

# --- Decorador para Cache ---
def cache_result(cache_key_func):
    """Decorator para cache de resultados de funções"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache_key_func(*args, **kwargs)
            try:
                # Tenta obter do cache
                if cache_key in search_cache:
                    logger.debug(f"Cache hit para key: {cache_key}")
                    return search_cache[cache_key]
            except Exception as e:
                logger.warning(f"Falha ao acessar cache para key {cache_key}: {e}")
            try:
                # Executa a função e armazena no cache
                result = func(*args, **kwargs)
                try:
                    search_cache[cache_key] = result
                    logger.debug(f"Cache miss para key: {cache_key} (armazenado)")
                except Exception as e:
                    logger.warning(f"Falha ao salvar no cache para key {cache_key}: {e}")
                return result
            except Exception as e:
                logger.error(f"Erro na função decorada por cache_result: {e}")
                raise
        return wrapper
    return decorator

# --- Classes de Erro Customizadas ---
class ValidationError(Exception):
    """Erro de validação de dados"""
    """Erro de validação de dados"""
    # Pode ser expandido para incluir informações adicionais no futuro
    pass

class ServiceUnavailableError(Exception):
    """Erro de serviço indisponível"""
    """Erro de serviço indisponível"""
    # Pode ser expandido para incluir informações adicionais no futuro
    pass

class KnowledgeBaseError(Exception):
    """Erro na base de conhecimento"""
    """Erro na base de conhecimento"""
    # Pode ser expandido para incluir informações adicionais no futuro
    pass

# --- Definição das Ferramentas Melhoradas ---
# Funções wrapper com validação centralizada e tratamento de erro robusto

def create_transfer_tool(tool_class, tool_name):
    """Factory function para criar ferramentas de transferência com validação centralizada"""
    def transfer_tool(conversation_id: str):
        """Ferramenta para transferir conversa usando validação centralizada."""
        logger.info(f"{tool_name}_tool chamado com conversation_id={conversation_id}")

        try:
            if not validate_conversation_id(conversation_id):
                error_msg = f"conversation_id inválido: {conversation_id}. Use o valor EXATO do contexto recebido."
                logger.error(error_msg)
                return {"error": error_msg}

            return tool_class().run({"conversation_id": conversation_id})

        except Exception as e:
            logger.error(f"Erro em {tool_name}_tool: {str(e)}")
            return {"error": f"Erro interno: {str(e)}"}

    transfer_tool.__name__ = tool_name
    return transfer_tool

# Cria as ferramentas de transferência usando a factory
suporte_tool = create_transfer_tool(SuporteTool, "suporte")
cadastros_tool = create_transfer_tool(CadastrosTool, "cadastros")
duvidas_tool = create_transfer_tool(DuvidasTool, "duvidas")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ValidationError, ServiceUnavailableError))
)
@circuit_breaker(max_failures=3, timeout=60)
def atribui_cidade_tool(contact_id: str, cidade: str):
    """Ferramenta para atribuir cidade ao contato no Chatwoot com validação robusta."""
    logger.info(f"atribui_cidade_tool chamado com contact_id={contact_id}, cidade={cidade}")

    try:
        # Validação do contact_id
        if not validate_contact_id(contact_id):
            error_msg = f"contact_id inválido: {contact_id}. Use apenas o ID do contexto atual."
            logger.error(error_msg)
            raise ValidationError(error_msg)

        # Obtém cidades válidas da configuração
        cidades_validas = AppConfig.load_valid_cities()

        # Verifica cache para normalização de cidade
        cache_key = f"city_norm_{cidade.lower().strip()}"
        if cache_key in city_cache:
            cidade_final = city_cache[cache_key]
            logger.info(f"Cidade normalizada do cache: '{cidade}' -> '{cidade_final}'")
        else:
            # Normaliza a entrada do usuário
            cidade_normalizada = cidade.lower().strip()

            if cidade_normalizada in cidades_validas:
                cidade_final = cidades_validas[cidade_normalizada]
                city_cache[cache_key] = cidade_final
                logger.info(f"Cidade normalizada: '{cidade}' -> '{cidade_final}'")
            else:
                error_msg = f"Cidade inválida: '{cidade}'. Cidades aceitas: {list(set(cidades_validas.values()))}"
                logger.error(error_msg)
                raise ValidationError(error_msg)

        return AtribuiCidadeTool().run({"contact_id": contact_id, "cidade": cidade_final})

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Erro em atribui_cidade_tool: {str(e)}")
        raise ServiceUnavailableError(f"Erro ao atribuir cidade: {str(e)}")

atribui_cidade_tool.__name__ = "atribui_a_cidade"

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ValidationError, ServiceUnavailableError))
)
def contato_categoria_tool(contact_id: str, categoria: str):
    """Ferramenta para atribuir categoria de atendimento ao contato no Chatwoot."""
    logger.info(f"contato_categoria_tool chamado com contact_id={contact_id}, categoria={categoria}")

    try:
        # Validação da categoria
        if not validate_category(categoria):
            error_msg = f"Categoria inválida: {categoria}. Use apenas: Passageiro ou Motorista."
            logger.error(error_msg)
            raise ValidationError(error_msg)

        # Validação do contact_id
        if not validate_contact_id(contact_id):
            error_msg = f"contact_id inválido: {contact_id}. Use o valor EXATO do contexto."
            logger.error(error_msg)
            raise ValidationError(error_msg)

        return ContatoCategoriaTool().run({"contact_id": contact_id, "categoria": categoria})

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Erro em contato_categoria_tool: {str(e)}")
        raise ServiceUnavailableError(f"Erro ao atribuir categoria: {str(e)}")

contato_categoria_tool.__name__ = "contato_categoria"

@cache_result(lambda query: f"duckduckgo_{hash(query)}")
@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=2, max=5),
    retry=retry_if_exception_type(ServiceUnavailableError)
)
def busca_duckduckgo_tool(query: str):
    """
    Ferramenta de busca DuckDuckGo para informações complementares com cache e retry.
    """
    logger.info(f"busca_duckduckgo_tool chamado com query={query}")

    try:
        return duckduckgo_search(query)
    except Exception as e:
        logger.error(f"Erro em busca_duckduckgo_tool: {str(e)}")
        raise ServiceUnavailableError(f"Erro na busca DuckDuckGo: {str(e)}")

busca_duckduckgo_tool.__name__ = "busca_duckduckgo"

# --- Configuração do Agente Melhorado ---
os.makedirs("tmp", exist_ok=True)
agent_storage = AppConfig.AGENT_STORAGE_PATH

# --- INICIALIZAÇÃO AUTOMÁTICA DA BASE DE CONHECIMENTO ---
def ensure_knowledge_base_startup():
    logger.info("[STARTUP] Base de conhecimento RAG via pgvector será usada. Nenhuma inicialização local necessária.")
    return True

# --- Ferramenta profissional de busca RAG ---
def busca_knowledge_base_tool(query: str):
    """
    Busca na base vetorizada via pgvector (RAG profissional).
    Retorna o documento mais relevante ou mensagem de não encontrado.
    """
    logger.info(f"[RAG] busca_knowledge_base_tool chamado com query={query}")
    results = retrieve_similar_documents(query, top_k=1)
    if results:
        doc_id, content, title, distance = results[0]
        return {
            "found": True,
            "source": "knowledge_pgvector",
            "title": title,
            "content": content,
            "distance": distance,
            "doc_id": doc_id
        }
    else:
        return {
            "found": False,
            "message": "Informação não encontrada na base vetorizada"
        }

# --- Melhorias na Memória do Agente sem Aumentar Histórico ---
class MemoryOptimizedAgent(Agent):
    """
    Agente com memória otimizada que não depende apenas do histórico de mensagens.
    Implementa:
    1. Memória semântica baseada em embeddings (simulado)
    2. Memória de fatos extraídos das conversas
    3. Memória de contexto persistente
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.semantic_memory = {}  # Memória semântica (conceitos)
        self.factual_memory = {}   # Memória de fatos (informações específicas)
        self.context_memory = {}   # Memória de contexto por sessão

    def extract_facts_from_conversation(self, message: str, session_id: str) -> List[str]:
        """Extrai fatos importantes da mensagem do usuário"""
        facts = []
        patterns = {
            "cidade": r"(?:mor[oa]|resido|vivo|estou) em ([\w\s]+)|de ([\w\s]+)|cidade(?: é)? ([\w\s]+)",
            "categoria": r"sou (passageiro|motorista)|atendimento como (passageiro|motorista)|como (passageiro|motorista)",
            "contato": r"meu (telefone|celular|email) é ([\w\s@.]+)",
            "problema": r"problema com ([\w\s]+)|erro ([\w\s]+)|não consigo ([\w\s]+)"
        }
        import re
        for fact_type, pattern in patterns.items():
            matches = re.findall(pattern, message.lower())
            if matches:
                for match in matches:
                    fact_value = next((m for m in match if m.strip()), "")
                    if fact_value:
                        facts.append(f"{fact_type}: {fact_value}")
        return facts

    def extract_city_and_category(self, message: str) -> dict:
        """Extrai e normaliza cidade e categoria da mensagem do usuário"""
        result = {}
        # Cidade
        city_patterns = r"(?:mor[oa]|resido|vivo|estou) em ([\w\s]+)|de ([\w\s]+)|cidade(?: é)? ([\w\s]+)"
        import re
        city_matches = re.findall(city_patterns, message.lower())
        if city_matches:
            city_raw = next((m for match in city_matches for m in match if m.strip()), None)
            if city_raw:
                cidades_validas = AppConfig.load_valid_cities()
                city_norm = city_raw.lower().strip()
                if city_norm in cidades_validas:
                    result["cidade"] = cidades_validas[city_norm]
        # Categoria
        cat_patterns = r"sou (passageiro|motorista)|atendimento como (passageiro|motorista)|como (passageiro|motorista)"
        cat_matches = re.findall(cat_patterns, message.lower())
        if cat_matches:
            cat_raw = next((m for match in cat_matches for m in match if m.strip()), None)
            if cat_raw:
                cat_norm = cat_raw.capitalize()
                if validate_category(cat_norm):
                    result["categoria"] = cat_norm
        return result

    def update_memory(self, message: str, session_id: str, context: dict = None):
        """Atualiza as diferentes memórias do agente e integra extração automática de cidade e categoria"""
        facts = self.extract_facts_from_conversation(message, session_id)
        # Atualiza memória de fatos
        if session_id not in self.factual_memory:
            self.factual_memory[session_id] = set()
        for fact in facts:
            self.factual_memory[session_id].add(fact)
            logger.debug(f"Fato extraído e armazenado: {fact}")

        # Atualiza memória de contexto
        if session_id not in self.context_memory:
            self.context_memory[session_id] = {}

        # Integra extração automática de cidade e categoria com logging e fallback
        extracted = self.extract_city_and_category(message)
        if extracted.get("cidade"):
            self.context_memory[session_id]["custom_attributes_city"] = extracted["cidade"]
            logger.info(f"[MEMORY] Cidade extraída automaticamente: '{extracted['cidade']}' para sessão {session_id}")
        else:
            logger.warning(f"[MEMORY][FALLBACK] Não foi possível extrair/normalizar cidade da mensagem: '{message}' (sessão {session_id})")
        if extracted.get("categoria"):
            self.context_memory[session_id]["custom_attributes_category"] = extracted["categoria"]
            logger.info(f"[MEMORY] Categoria extraída automaticamente: '{extracted['categoria']}' para sessão {session_id}")
        else:
            logger.warning(f"[MEMORY][FALLBACK] Não foi possível extrair/normalizar categoria da mensagem: '{message}' (sessão {session_id})")

        # Mantém informações importantes do contexto recebido
        if context:
            important_keys = ["custom_attributes_city", "custom_attributes_category", "contact_id", "conversation_id"]
            for key in important_keys:
                if key in context and context[key]:
                    self.context_memory[session_id][key] = context[key]

    def get_relevant_memory(self, session_id: str, query: str) -> str:
        """Recupera memória relevante para a consulta atual"""
        memory_parts = []

        # Memória factual
        if session_id in self.factual_memory and self.factual_memory[session_id]:
            memory_parts.append("Fatos conhecidos:")
            for fact in self.factual_memory[session_id]:
                memory_parts.append(f"- {fact}")

        # Memória de contexto
        if session_id in self.context_memory and self.context_memory[session_id]:
            memory_parts.append("Contexto persistente:")
            for key, value in self.context_memory[session_id].items():
                memory_parts.append(f"- {key}: {value}")

        return "\n".join(memory_parts) if memory_parts else ""

    def run(self, message, session_id=None, context=None, **kwargs):
        """Override do método run para incluir memória otimizada"""
        # Atualiza memória antes de processar
        if session_id:
            self.update_memory(message, session_id, context)

        # Obtém memória relevante
        relevant_memory = self.get_relevant_memory(session_id or "default", message)

        # Adiciona memória relevante ao contexto
        enhanced_context = context.copy() if context else {}
        if relevant_memory:
            enhanced_context["agent_memory"] = relevant_memory

        # Chama o método original com contexto aprimorado
        return super().run(message=message, session_id=session_id, context=enhanced_context, **kwargs)

# INSTRUÇÕES SIMPLIFICADAS: Concisas e diretas como no n8n
alice_instructions = [
    "Você é Alice, assistente virtual da Urban. Seja humana, calorosa e prestativa.",
    "SEMPRE use dados do contexto atual PRIMEIRO. Nunca pergunte informações já presentes no contexto.",
    "🔴 REGRA CRÍTICA DE VALIDAÇÃO DE ATRIBUTOS (flags booleanas):",
    "- Se cidade_preenchida=True: NUNCA pergunte a cidade, nem em saudações, nem em qualquer contexto. Apenas cumprimente ou responda normalmente.",
    "- Se categoria_preenchida=True: NUNCA pergunte a categoria, nem em saudações, nem em qualquer contexto.",
    "- Se cidade_preenchida=False: SEMPRE pergunte a cidade no final da resposta.",
    "- Se categoria_preenchida=False E cidade_preenchida=True: SEMPRE pergunte APENAS a categoria.",
    "CATEGORIZAÇÃO SEQUENCIAL: REGRA DE OURO - Pergunte UMA coisa por vez, SEMPRE, mesmo em saudações, empatia ou qualquer contexto:",
    "1. Se cidade_preenchida=False: Responda a pergunta ou cumprimente normalmente, MAS SEMPRE pergunte APENAS a cidade no final se 'cidade_preenchida': False . Exemplo: 'Bom dia! Como posso ajudar você hoje? Só preciso saber, de qual cidade você está falando?'",
    "2. Se categoria_preenchida=False E cidade_preenchida=True: Pergunte APENAS a categoria. Exemplo: 'Seu atendimento é como Passageiro ou Motorista?'",
    "3. Se cidade_preenchida=True E categoria_preenchida=True: Responda normalmente SEM perguntar cidade ou categoria. Exemplo: 'Olá! Como posso ajudar você hoje?'",
    "4. NUNCA faça as duas perguntas na mesma mensagem. Sempre uma por vez, em sequência.",
    "5. NUNCA encerre uma resposta sem perguntar cidade ou categoria se cidade_preenchida ou categoria_preenchida forem False, mesmo em mensagens de empatia, saudação ou conversa social. Isso é prioridade máxima.",
    "EXEMPLO DE CONTEXTO CORRETO (não perguntar cidade): contexto = {'cidade_preenchida': True, 'categoria_preenchida': True, ...} → Responda apenas: 'Olá! Como posso ajudar você hoje?' (NÃO pergunte cidade nem categoria)",
    "EXEMPLO DE CONTEXTO QUE DEVE PERGUNTAR CIDADE: contexto = {'cidade_preenchida': False, ...} → Pergunte a cidade no final.",
    "EXEMPLO DE CONTEXTO QUE DEVE PERGUNTAR CATEGORIA: contexto = {'cidade_preenchida': True, 'categoria_preenchida': False, ...} → Pergunte apenas a categoria.",
    "CONHECIMENTO: SEMPRE consulte PRIMEIRO a base de conhecimento local usando `busca_knowledge_base` antes de qualquer outra ferramenta.",
    "BUSCA INTELIGENTE: Se a base local não tiver a resposta, use `busca_duckduckgo` para horários de transporte, localizações, problemas técnicos ou informações sobre cidades.",
    "Ao usar a ferramenta busca_duckduckgo, sempre formule a query de forma descritiva e enciclopédica, incluindo contexto, unidade de medida ou idioma alternativo se necessário. Exemplo: 'altura da torre eiffel em metros', 'história da Urban', 'Eiffel Tower height in meters'. Se não houver resposta, tente uma variação mais detalhada ou em inglês.",
    "🔴 REGRA CRÍTICA DE IDS - USE SEMPRE AS VARIÁVEIS EXPLÍCITAS DO CONTEXTO:",
    "- Para ferramentas de transferência (suporte, cadastros, duvidas): use o valor de CONVERSATION_ID_ATUAL do contexto",
    "- Para ferramentas de atribuição (atribui_cidade, contato_categoria): use o valor de CONTACT_ID_ATUAL do contexto",
    "- NUNCA invente IDs, NUNCA use valores de exemplo, SEMPRE use APENAS o valor real de CONTACT_ID_ATUAL e CONVERSATION_ID_ATUAL extraído do contexto da payload. Sempre use exatamente o valor recebido, nunca um exemplo fixo.",
    "ATRIBUIÇÃO DE CIDADE - REGRA CRÍTICA: Para atribuir cidade, use APENAS os nomes EXATOS desta lista (sem acento, primeira letra maiúscula): Matupa, Guaranta, Peixoto, Monte Verde, Bandeirantes, Alta Floresta, Nova Canaa, Colider. Se usuário disser variações como 'Matupá', 'peixoto', 'alta floresta', normalize para o nome EXATO da lista (Matupa, Peixoto, Alta Floresta). NUNCA use nomes diferentes desta lista.",
    "FORMATO CIDADE: Sempre use atribui_cidade_tool(contact_id=CONTACT_ID_ATUAL, cidade='Matupa') com nome EXATO da lista, nunca use JSON ou outros formatos.",
    "Responda diretamente usando conhecimento quando possível. Use busca_knowledge_base como primeira opção, busca_duckduckgo como segunda opção. Só ofereça transferência como último recurso.",
    "MEMÓRIA: Use informações da memória do agente (fatos e contexto persistente) para personalizar respostas e evitar perguntas repetitivas.",
]

# Função para transformar o contexto em texto dinâmico
def contexto_para_texto(context: dict) -> str:
    def sim_nao(val):
        return "Sim" if val else "Não"
    linhas = ["[CONTEXT]"]
    if context.get("user_id"): linhas.append(f"Usuário: {context.get('user_id')}")
    if context.get("contact_id"): linhas.append(f"Contact ID: {context.get('contact_id')}")
    if context.get("conversation_id"): linhas.append(f"Conversation ID: {context.get('conversation_id')}")
    if context.get("custom_attributes_city"): linhas.append(f"Cidade: {context.get('custom_attributes_city')}")
    if context.get("custom_attributes_category"): linhas.append(f"Categoria: {context.get('custom_attributes_category')}")
    if "CIDADE_JA_INFORMADA" in context:
        linhas.append(f"Cidade já informada: {sim_nao(context.get('CIDADE_JA_INFORMADA'))}")
    if "CATEGORIA_JA_INFORMADA" in context:
        linhas.append(f"Categoria já informada: {sim_nao(context.get('CATEGORIA_JA_INFORMADA'))}")

    # Adiciona memória do agente se disponível
    if context.get("agent_memory"):
        linhas.append("[AGENT_MEMORY]")
        linhas.append(context.get("agent_memory"))
        linhas.append("[/AGENT_MEMORY]")

    linhas.append("[/CONTEXT]\n")
    return "\n".join(linhas)

# Wrapper para garantir que o prompt sempre começa com o contexto textual
class AliceAgentWithContext(MemoryOptimizedAgent):
    def run(self, message, session_id=None, context=None, **kwargs):
        context = context or {}
        contexto_textual = contexto_para_texto(context)
        # Junta contexto, instruções e mensagem do usuário
        prompt = f"{contexto_textual}\n" + "\n".join(alice_instructions) + f"\n\nUsuário: {message}"
        # Chama o modelo com o prompt montado
        return super().run(message=prompt, session_id=session_id, context=context, **kwargs)

alice_agent = AliceAgentWithContext(
    name="Alice",
    model=OpenAIChat(id="gpt-4o", api_key=api_key),
    tools=[
        busca_knowledge_base_tool,
        suporte_tool,
        cadastros_tool,
        duvidas_tool,
        atribui_cidade_tool,
        contato_categoria_tool,
        busca_duckduckgo_tool
    ],
    instructions=alice_instructions,
    add_history_to_messages=True,
    num_history_responses=3,  # Mantido baixo, mas com memória otimizada
    markdown=True,
)

# --- Playground Customizado Melhorado ---

class EmotionData(BaseModel):
    emocao_primaria: Optional[str] = None
    sentimento: Optional[str] = None
    justificativa: Optional[str] = None

class CustomRunPayload(BaseModel):
    message: str
    session_id: str
    user_id: Optional[str] = None
    contact_id: Optional[str] = None
    dados_emocao: Optional[EmotionData] = Field(None, alias="dados_emocao")
    conversation_id: Optional[str] = None
    custom_attributes_city: Optional[str] = None
    custom_attributes_category: Optional[str] = None

    @validator('conversation_id')
    def validate_conversation_id_field(cls, v):
        if v and not validate_conversation_id(v):
            raise ValueError('conversation_id inválido')
        return v

    @validator('contact_id')
    def validate_contact_id_field(cls, v):
        if v and not validate_contact_id(v):
            raise ValueError('contact_id inválido')
        return v

class CustomPlayground(Playground):
    def get_app(self):
        app = super().get_app()

        # Adiciona middlewares
        app.add_middleware(GZipMiddleware)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        app.state.agents = {agent.name: agent for agent in self.agents}
        app.state.limiter = limiter

        routes_to_keep = [
            route for route in app.routes if getattr(route, "path", "") != "/v1/playground/agents/{agent_id}/runs"
        ]
        app.router.routes = routes_to_keep

        @app.exception_handler(RateLimitExceeded)
        async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests", "message": "Limite de requisições excedido. Tente novamente mais tarde."}
            )

        @app.exception_handler(ValidationError)
        async def validation_exception_handler(request: Request, exc: ValidationError):
            return JSONResponse(
                status_code=400,
                content={"detail": "Validation Error", "message": str(exc)}
            )

        @app.exception_handler(ServiceUnavailableError)
        async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError):
            return JSONResponse(
                status_code=503,
                content={"detail": "Service Unavailable", "message": str(exc)}
            )

        @app.post("/v1/playground/agents/{agent_id}/runs", tags=["Playground"])
        @limiter.limit("100/minute")
        def run_agent_custom(agent_id: str, payload: CustomRunPayload, request: Request):
            start_time = time.time()
            logger.info(f"Requisição recebida - Agent: {agent_id}, Session: {payload.session_id}")

            agents_dict: Dict[str, Agent] = request.app.state.agents
            agent = agents_dict.get(agent_id)
            if not agent:
                logger.error(f"Agente não encontrado: {agent_id}")
                raise HTTPException(status_code=404, detail=f"Agent with ID '{agent_id}' not found.")

            # EXTRAÇÃO CRÍTICA: Quebra payload em variáveis explícitas para garantir uso correto
            current_conversation_id = payload.conversation_id
            current_contact_id = payload.contact_id
            current_user_id = payload.user_id
            current_city = payload.custom_attributes_city
            current_category = payload.custom_attributes_category

            context = {
                "user_id": current_user_id,
                "contact_id": current_contact_id,
                "dados_emocao": payload.dados_emocao.model_dump() if payload.dados_emocao else None,
                "conversation_id": current_conversation_id,
                "custom_attributes_city": current_city,
                "custom_attributes_category": current_category,
                # VARIÁVEIS EXPLÍCITAS: Para garantir que o agente sempre use os valores corretos
                "CONVERSATION_ID_ATUAL": current_conversation_id,
                "CONTACT_ID_ATUAL": current_contact_id,
                "USER_ID_ATUAL": current_user_id,
                "CIDADE_ATUAL": current_city,
                "CATEGORIA_ATUAL": current_category,
                # VALIDAÇÕES CRÍTICAS: Determina se cidade e categoria estão realmente presentes
                "CIDADE_JA_INFORMADA": bool(current_city and current_city.strip() and current_city.strip() != ""),
                "CATEGORIA_JA_INFORMADA": bool(current_category and current_category.strip() and current_category.strip() != ""),
            }

            logger.debug(f"Contexto recebido no endpoint: {context}")
            logger.debug(f"Variáveis extraídas: conversation_id={current_conversation_id}, contact_id={current_contact_id}")
            logger.debug(f"Validações: CIDADE_JA_INFORMADA={context['CIDADE_JA_INFORMADA']}, CATEGORIA_JA_INFORMADA={context['CATEGORIA_JA_INFORMADA']}")

            try:
                result = agent.run(
                    message=payload.message,
                    session_id=payload.session_id,
                    context=context
                )

                # Métricas de performance
                processing_time = time.time() - start_time
                logger.info(f"Requisição processada em {processing_time:.2f}s")

                # Retorno robusto: trata dict, objeto com .dict()/.model_dump(), ou string
                import collections.abc
                def to_json_safe(obj):
                    if isinstance(obj, (str, int, float, bool)) or obj is None:
                        return obj
                    if isinstance(obj, dict):
                        return {k: to_json_safe(v) for k, v in obj.items() if not callable(v)}
                    if isinstance(obj, (list, tuple, set)):
                        return [to_json_safe(v) for v in obj]
                    # Para objetos customizados, tenta converter para string
                    return str(obj)

                if hasattr(result, "dict"):
                    response_data = to_json_safe(result.dict())
                elif hasattr(result, "model_dump"):
                    response_data = to_json_safe(result.model_dump())
                elif isinstance(result, dict):
                    response_data = to_json_safe(result)
                else:
                    response_data = {"result": to_json_safe(result)}

                # Adiciona métricas à resposta
                response_data["processing_time"] = round(processing_time, 2)
                response_data["timestamp"] = datetime.now().isoformat()

                return response_data

            except Exception as e:
                logger.error(f"Erro ao processar requisição: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

        @app.get("/health", tags=["Health"])
        def health_check():
            """Health check endpoint para monitoramento com informações detalhadas"""
            return {
                "status": "healthy",
                "agent": "Alice",
                "tools": ["busca_knowledge_base", "suporte", "cadastros", "duvidas", "atribui_a_cidade", "contato_categoria", "busca_duckduckgo"],
                "version": "3.0",
                "features": ["chatwoot_integration", "knowledge_base", "duckduckgo_search", "intelligent_fallback", "optimized_memory", "circuit_breaker", "rate_limiting"],
                "timestamp": datetime.now().isoformat()
            }

        @app.get("/debug/memory/{session_id}", tags=["Debug"])
        def debug_agent_memory(session_id: str):
            """Debug endpoint para verificar memória do agente"""
            try:
                if not hasattr(alice_agent, 'factual_memory'):
                    return {"status": "not_implemented", "message": "Memória do agente não disponível"}

                factual_memory = alice_agent.factual_memory.get(session_id, set())
                context_memory = alice_agent.context_memory.get(session_id, {})

                return {
                    "status": "success",
                    "session_id": session_id,
                    "factual_memory": list(factual_memory),
                    "context_memory": context_memory,
                    "factual_memory_count": len(factual_memory)
                }
            except Exception as e:
                logger.error(f"Erro ao acessar memória do agente: {str(e)}")
                return {
                    "status": "error",
                    "error": str(e),
                    "message": f"Erro ao acessar memória: {e}"
                }

        @app.get("/debug/cache", tags=["Debug"])
        def debug_cache():
            """Debug endpoint para verificar status do cache"""
            return {
                "search_cache": {
                    "size": len(search_cache),
                    "maxsize": search_cache.maxsize,
                    "ttl": search_cache.ttl
                },
                "city_cache": {
                    "size": len(city_cache),
                    "maxsize": city_cache.maxsize,
                    "ttl": city_cache.ttl
                }
            }

        @app.post("/debug/cache/clear", tags=["Debug"])
        def clear_cache():
            """Limpa todos os caches"""
            search_cache.clear()
            city_cache.clear()
            logger.info("Cache limpo")
            return {"status": "success", "message": "Cache limpo com sucesso"}

        return app

# --- Inicialização do App ---
ensure_knowledge_base_startup()
logger.info("✅ Base de conhecimento RAG (pgvector) configurada para produção")

# Cria diretório de configuração se não existir
os.makedirs("config", exist_ok=True)

# Salva configuração de cidades se não existir
cities_file = "config/cidades.json"
if not os.path.exists(cities_file):
    try:
        with open(cities_file, 'w', encoding='utf-8') as f:
            json.dump(AppConfig.load_valid_cities(), f, indent=2, ensure_ascii=False)
        logger.info(f"Arquivo de configuração de cidades criado: {cities_file}")
    except Exception as e:
        logger.error(f"Erro ao criar arquivo de configuração de cidades: {e}")

playground_app = CustomPlayground(agents=[alice_agent])
app = playground_app.get_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Iniciando servidor na porta {port}")
    uvicorn.run("playground:app", host="0.0.0.0", port=port, reload=False)
