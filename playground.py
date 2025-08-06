import os
from dotenv import load_dotenv
from fastapi import Body, FastAPI, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.playground import Playground
from agno.storage.sqlite import SqliteStorage

# Importe suas ferramentas customizadas
from tools.suporte_tool import SuporteTool
from tools.cadastros_tool import CadastrosTool
from tools.duvidas_tool import DuvidasTool
from tools.atribui_cidade_tool import AtribuiCidadeTool
from tools.contato_categoria_tool import ContatoCategoriaTool
from tools.duckduckgo_search_tool import duckduckgo_search

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# --- Definição das Ferramentas ---
# Funções wrapper para garantir que as ferramentas sejam registradas corretamente no Agno

def suporte_tool(conversation_id: str):
    """Ferramenta para transferir conversa para o time de suporte no Chatwoot. Requer 'conversation_id'."""
    print(f"[LOG] suporte_tool chamado com conversation_id={conversation_id}")
    print(f"[DEBUG] Valor recebido: '{conversation_id}' (tipo: {type(conversation_id)})")
    assert conversation_id is not None, "conversation_id não pode ser None!"

    # VALIDAÇÃO CRÍTICA: Bloqueia IDs que não são strings numéricas simples (evita IDs longos incorretos)
    if not conversation_id.isdigit() or len(conversation_id) > 6:
        print(f"[ERRO] conversation_id inválido ou muito longo: {conversation_id}. Bloqueando chamada.")
        print(f"[DICA] Use o valor EXATO de conversation_id recebido no contexto, sem variáveis ou exemplos.")
        return {"error": f"conversation_id inválido: {conversation_id}. Use o valor EXATO do contexto recebido."}

    return SuporteTool().run({"conversation_id": conversation_id})
suporte_tool.__name__ = "suporte"


def cadastros_tool(conversation_id: str):
    """Ferramenta para transferir conversa para o time de cadastros no Chatwoot. Requer 'conversation_id'."""
    print(f"[LOG] cadastros_tool chamado com conversation_id={conversation_id}")
    print(f"[DEBUG] Valor recebido: '{conversation_id}' (tipo: {type(conversation_id)})")
    assert conversation_id is not None, "conversation_id não pode ser None!"

    # VALIDAÇÃO CRÍTICA: Bloqueia IDs que não são strings numéricas simples (evita IDs longos incorretos)
    if not conversation_id.isdigit() or len(conversation_id) > 6:
        print(f"[ERRO] conversation_id inválido ou muito longo: {conversation_id}. Bloqueando chamada.")
        print(f"[DICA] Use o valor EXATO de conversation_id recebido no contexto, sem variáveis ou exemplos.")
        return {"error": f"conversation_id inválido: {conversation_id}. Use o valor EXATO do contexto recebido."}

    return CadastrosTool().run({"conversation_id": conversation_id})
cadastros_tool.__name__ = "cadastros"


def duvidas_tool(conversation_id: str):
    """Ferramenta para transferir conversa para o time de dúvidas gerais no Chatwoot. Requer 'conversation_id'."""
    print(f"[LOG] duvidas_tool chamado com conversation_id={conversation_id}")
    print(f"[DEBUG] Valor recebido: '{conversation_id}' (tipo: {type(conversation_id)})")
    assert conversation_id is not None, "conversation_id não pode ser None!"

    # VALIDAÇÃO CRÍTICA: Bloqueia IDs que não são strings numéricas simples (evita IDs longos incorretos)
    if not conversation_id.isdigit() or len(conversation_id) > 6:
        print(f"[ERRO] conversation_id inválido ou muito longo: {conversation_id}. Bloqueando chamada.")
        print(f"[DICA] Use o valor EXATO de conversation_id recebido no contexto, sem variáveis ou exemplos.")
        return {"error": f"conversation_id inválido: {conversation_id}. Use o valor EXATO do contexto recebido."}

    return DuvidasTool().run({"conversation_id": conversation_id})
duvidas_tool.__name__ = "duvidas"

def atribui_cidade_tool(contact_id: str, cidade: str):
    """Ferramenta para atribuir cidade ao contato no Chatwoot. Requer 'contact_id' e 'cidade'."""
    print(f"[LOG] atribui_cidade_tool chamado com contact_id={contact_id}, cidade={cidade}")

    # VALIDAÇÃO CRÍTICA: Bloqueia contact_id inválidos como 'undefined'
    if contact_id == "undefined" or not contact_id or not contact_id.isdigit():
        print(f"[ERRO] contact_id inválido: {contact_id}. Bloqueando chamada.")
        return {"error": f"contact_id inválido: {contact_id}. Use apenas o ID do contexto atual."}

    # NORMALIZAÇÃO CRÍTICA DE CIDADE: Lista exata de cidades aceitas pela API
    cidades_validas = {
        # Mapeamento de variações para nomes EXATOS da API
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

    # Normaliza a entrada do usuário
    cidade_normalizada = cidade.lower().strip()

    if cidade_normalizada in cidades_validas:
        cidade_final = cidades_validas[cidade_normalizada]
        print(f"[LOG] Cidade normalizada de '{cidade}' para '{cidade_final}'")
    else:
        print(f"[ERRO] Cidade inválida: '{cidade}'. Cidades aceitas: {list(set(cidades_validas.values()))}")
        return {"error": f"Cidade inválida: '{cidade}'. Cidades aceitas: Matupa, Guaranta, Peixoto, Monte Verde, Bandeirantes, Alta Floresta, Nova Canaa, Colider"}

    return AtribuiCidadeTool().run({"contact_id": contact_id, "cidade": cidade_final})
atribui_cidade_tool.__name__ = "atribui_a_cidade"

def contato_categoria_tool(contact_id: str, categoria: str):
    """Ferramenta para atribuir categoria de atendimento ao contato no Chatwoot. Aceita apenas 'Passageiro' ou 'Motorista'. Requer 'contact_id' e 'categoria'."""
    print(f"[LOG] contato_categoria_tool chamado com contact_id={contact_id}, categoria={categoria}")

    # VALIDAÇÃO CRÍTICA: Só aceita categorias válidas
    categorias_validas = ["Passageiro", "Motorista"]
    if categoria not in categorias_validas:
        print(f"[ERRO] Categoria inválida: {categoria}. Use apenas: {categorias_validas}")
        return f"Categoria inválida: {categoria}. Use apenas: Passageiro ou Motorista."

    # VALIDAÇÃO CRÍTICA: contact_id deve ser válido
    if not contact_id or not contact_id.isdigit():
        print(f"[ERRO] contact_id inválido: {contact_id}. Bloqueando chamada.")
        return f"contact_id inválido: {contact_id}. Use o valor EXATO do contexto."

    return ContatoCategoriaTool().run({"contact_id": contact_id, "categoria": categoria})
contato_categoria_tool.__name__ = "contato_categoria"

def busca_duckduckgo_tool(query: str):
    """
    Ferramenta de busca DuckDuckGo para informações complementares.

    Use quando:
    - A base de conhecimento não tiver a resposta
    - Usuário perguntar sobre horários de transporte, localizações específicas
    - Problemas técnicos que precisam de soluções atualizadas
    - Informações sobre cidades específicas da região
    """
    print(f"[LOG] busca_duckduckgo_tool chamado com query={query}")
    return duckduckgo_search(query)
busca_duckduckgo_tool.__name__ = "busca_duckduckgo"

# --- Configuração do Agente ---
os.makedirs("tmp", exist_ok=True)
agent_storage = "tmp/agents.db"

# --- INICIALIZAÇÃO AUTOMÁTICA DA BASE DE CONHECIMENTO ---
def ensure_knowledge_base_startup():
    """
    Garante que a base de conhecimento esteja populada na inicialização.
    Crítico para deployment em produção onde o banco pode estar vazio.
    """
    print(f"[STARTUP] Verificando base de conhecimento...")

    try:
        # Verifica se já existe dados na base
        storage = SqliteStorage(table_name="knowledge", db_file=agent_storage)
        existing_sessions = storage.get_all_sessions()

        if existing_sessions and len(existing_sessions) > 0:
            print(f"[STARTUP] ✅ Base de conhecimento OK com {len(existing_sessions)} documentos")
            return True

        print(f"[STARTUP] ⚠️  Base de conhecimento vazia. Importando dados...")

        # Importa dados do knowledge_base.md
        knowledge_file = "knowledge_base.md"
        if not os.path.exists(knowledge_file):
            print(f"[STARTUP] ❌ Arquivo knowledge_base.md não encontrado")
            return False

        # Lê e processa o arquivo markdown
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Divide por seções usando o padrão # Título
        from agno.storage.session.agent import AgentSession

        sections = []
        current_section = {"title": "", "content": ""}

        for line in content.split('\n'):
            if line.startswith('# ') and not line.startswith('##'):
                # Nova seção encontrada
                if current_section["title"]:  # Salva seção anterior se existir
                    sections.append(current_section)
                current_section = {
                    "title": line[2:].strip(),  # Remove '# '
                    "content": ""
                }
            else:
                # Adiciona linha ao conteúdo da seção atual
                current_section["content"] += line + '\n'

        # Adiciona a última seção
        if current_section["title"]:
            sections.append(current_section)

        # Insere seções no banco usando AgentSession
        for i, section in enumerate(sections):
            if section["title"] and section["content"].strip():
                session = AgentSession(
                    session_id=f"kb_{i+1}",
                    agent_id="knowledge_base",
                    user_id="system"
                )

                # Armazena os dados da seção no session_data
                session.session_data = {
                    "title": section["title"],
                    "content": section["content"].strip()
                }

                storage.upsert(session)

        # Verifica se a importação funcionou
        final_sessions = storage.get_all_sessions()
        print(f"[STARTUP] ✅ Base de conhecimento importada! {len(final_sessions)} documentos inseridos.")

        return True

    except Exception as e:
        print(f"[STARTUP] ❌ Erro ao garantir base de conhecimento: {e}")
        import traceback
        print(f"[STARTUP] Traceback: {traceback.format_exc()}")
        return False

# Executa a verificação da base de conhecimento na inicialização
ensure_knowledge_base_startup()

# --- Ferramenta de busca na base de conhecimento local ---
def busca_knowledge_base_tool(query: str):
    """
    Busca na base de conhecimento local da Urban usando palavras-chave no título ou conteúdo.

    Use esta ferramenta PRIMEIRO para responder perguntas sobre:
    - Propósito da Urban
    - Sistema de créditos
    - Cadastro de motorista e passageiro
    - Segurança
    - Política de adesivos
    - Área de atuação
    - Categorias Popular e Ofereça seu Preço
    - Qualquer informação específica da Urban
    """
    print(f"[LOG] busca_knowledge_base_tool chamado com query={query}")

    try:
        # Conecta na mesma tabela que o script de importação usa
        storage = SqliteStorage(table_name="knowledge", db_file=agent_storage)

        # Busca por palavras-chave no título ou conteúdo (case-insensitive)
        query_lower = query.lower()
        print(f"[DEBUG] Query convertida para lowercase: {query_lower}")

        # Cria uma lista de palavras-chave da query para busca mais flexível
        keywords = [word.strip() for word in query_lower.split() if len(word.strip()) > 2]
        print(f"[DEBUG] Palavras-chave extraídas: {keywords}")

        # Usa o método get_all_sessions do SqliteStorage
        all_sessions = storage.get_all_sessions()
        print(f"[DEBUG] Total de sessões encontradas: {len(all_sessions) if all_sessions else 0}")

        # Filtra resultados que contenham qualquer palavra-chave no título ou conteúdo
        matches = []
        for session in all_sessions:
            if hasattr(session, 'session_data') and session.session_data:
                session_data = session.session_data
                title = session_data.get("title", "").lower()
                content = session_data.get("content", "").lower()

                # Busca flexível: se qualquer palavra-chave estiver no título ou conteúdo
                match_found = False
                match_reasons = []

                for keyword in keywords:
                    if keyword in title:
                        match_found = True
                        match_reasons.append(f"'{keyword}' no título")
                    elif keyword in content:
                        match_found = True
                        match_reasons.append(f"'{keyword}' no conteúdo")

                if match_found:
                    print(f"[DEBUG] MATCH encontrado! Título: '{session_data.get('title', '')}', Razões: {match_reasons}")
                    # Calcula relevância baseada no número de matches
                    relevance = len(match_reasons)
                    matches.append({
                        "title": session_data.get("title", ""),
                        "content": session_data.get("content", ""),
                        "relevance": relevance,
                        "match_reasons": match_reasons
                    })

        # Ordena por relevância (mais matches primeiro)
        matches.sort(key=lambda x: x["relevance"], reverse=True)
        print(f"[DEBUG] Total de matches encontrados: {len(matches)}")

        if matches:
            print(f"[LOG] Encontrados {len(matches)} resultados na knowledge base")
            best_match = matches[0]
            print(f"[LOG] Melhor resultado: '{best_match['title']}' (relevância: {best_match['relevance']})")
            # Retorna o resultado mais relevante
            return {
                "found": True,
                "source": "knowledge_base",
                "title": best_match["title"],
                "content": best_match["content"],
                "relevance": best_match["relevance"]
            }
        else:
            print(f"[LOG] Nenhum resultado encontrado na knowledge base para: {query}")
            print(f"[DEBUG] Tentativa com palavras-chave: {keywords}")
            return {
                "found": False,
                "message": "Informação não encontrada na base de conhecimento local"
            }

    except Exception as e:
        print(f"[ERRO] Erro ao buscar na knowledge base: {e}")
        import traceback
        print(f"[ERRO] Traceback completo: {traceback.format_exc()}")
        return {
            "found": False,
            "error": f"Erro na busca local: {str(e)}"
        }

busca_knowledge_base_tool.__name__ = "busca_knowledge_base"# INSTRUÇÕES SIMPLIFICADAS: Concisas e diretas como no n8n
alice_instructions = [
    "Você é Alice, assistente virtual da Urban. Seja humana, calorosa e prestativa.",
    "SEMPRE use dados do contexto atual PRIMEIRO. Nunca pergunte informações já presentes no contexto.",
    "🔴 REGRA CRÍTICA DE VALIDAÇÃO DE ATRIBUTOS (flags booleanas):",
    "- Se cidade_preenchida=True: NUNCA pergunte a cidade, nem em saudações, nem em qualquer contexto. Apenas cumprimente ou responda normalmente.",
    "- Se categoria_preenchida=True: NUNCA pergunte a categoria, nem em saudações, nem em qualquer contexto.",
    "- Se cidade_preenchida=False: SEMPRE pergunte a cidade no final da resposta.",
    "- Se categoria_preenchida=False E cidade_preenchida=True: SEMPRE pergunte APENAS a categoria.",
    "CATEGORIZAÇÃO SEQUENCIAL: REGRA DE OURO - Pergunte UMA coisa por vez, SEMPRE, mesmo em saudações, empatia ou qualquer contexto:",
    "1. Se cidade_preenchida=False: Responda a pergunta ou cumprimente normalmente, MAS SEMPRE pergunte APENAS a cidade no final. Exemplo: 'Bom dia! Como posso ajudar você hoje? Só preciso saber, de qual cidade você está falando?'",
    "2. Se categoria_preenchida=False E cidade_preenchida=True: Pergunte APENAS a categoria. Exemplo: 'Seu atendimento é como Passageiro ou Motorista?'",
    "3. Se cidade_preenchida=True E categoria_preenchida=True: Responda normalmente SEM perguntar cidade ou categoria. Exemplo: 'Olá! Como posso ajudar você hoje?'",
    "4. NUNCA faça as duas perguntas na mesma mensagem. Sempre uma por vez, em sequência.",
    "5. NUNCA encerre uma resposta sem perguntar cidade ou categoria se cidade_preenchida ou categoria_preenchida forem False, mesmo em mensagens de empatia, saudação ou conversa social. Isso é prioridade máxima.",
    "EXEMPLO DE CONTEXTO CORRETO (não perguntar cidade): contexto = {'cidade_preenchida': True, 'categoria_preenchida': True, ...} → Responda apenas: 'Olá! Como posso ajudar você hoje?' (NÃO pergunte cidade nem categoria)",
    "EXEMPLO DE CONTEXTO QUE DEVE PERGUNTAR CIDADE: contexto = {'cidade_preenchida': False, ...} → Pergunte a cidade no final.",
    "EXEMPLO DE CONTEXTO QUE DEVE PERGUNTAR CATEGORIA: contexto = {'cidade_preenchida': True, 'categoria_preenchida': False, ...} → Pergunte apenas a categoria.",
    "CONHECIMENTO: SEMPRE consulte PRIMEIRO a base de conhecimento local usando `busca_knowledge_base` antes de qualquer outra ferramenta.",
    "BUSCA INTELIGENTE: Se a base local não tiver a resposta, use `busca_duckduckgo` para horários de transporte, localizações, problemas técnicos ou informações sobre cidades.",
    "🔴 REGRA CRÍTICA DE IDs - USE SEMPRE AS VARIÁVEIS EXPLÍCITAS DO CONTEXTO:",
    "- Para ferramentas de transferência (suporte, cadastros, duvidas): use o valor de CONVERSATION_ID_ATUAL do contexto",
    "- Para ferramentas de atribuição (atribui_cidade, contato_categoria): use o valor de CONTACT_ID_ATUAL do contexto",
    "- EXEMPLO CORRETO: Se CONVERSATION_ID_ATUAL='112', use suporte_tool(conversation_id='112')",
    "- EXEMPLO CORRETO: Se CONTACT_ID_ATUAL='10', use atribui_cidade_tool(contact_id='10', cidade='Matupa')",
    "- NUNCA invente IDs, NUNCA use valores de exemplo, SEMPRE pegue de CONVERSATION_ID_ATUAL e CONTACT_ID_ATUAL",
    "ATRIBUIÇÃO DE CIDADE - REGRA CRÍTICA: Para atribuir cidade, use APENAS os nomes EXATOS desta lista (sem acento, primeira letra maiúscula): Matupa, Guaranta, Peixoto, Monte Verde, Bandeirantes, Alta Floresta, Nova Canaa, Colider. Se usuário disser variações como 'Matupá', 'peixoto', 'alta floresta', normalize para o nome EXATO da lista (Matupa, Peixoto, Alta Floresta). NUNCA use nomes diferentes desta lista.",
    "FORMATO CIDADE: Sempre use atribui_cidade_tool(contact_id=CONTACT_ID_ATUAL, cidade='Matupa') com nome EXATO da lista, nunca use JSON ou outros formatos.",
    "Responda diretamente usando conhecimento quando possível. Use busca_knowledge_base como primeira opção, busca_duckduckgo como segunda opção. Só ofereça transferência como último recurso.",
]

alice_agent = Agent(
    name="Alice",
    model=OpenAIChat(id="gpt-4o", api_key=api_key),  # Mudança para gpt-4o padrão do Agno
    tools=[
        busca_knowledge_base_tool,  # PRIMEIRA ferramenta: base local
        suporte_tool,
        cadastros_tool,
        duvidas_tool,
        atribui_cidade_tool,
        contato_categoria_tool,
        busca_duckduckgo_tool  # SEGUNDA opção: busca externa
    ],
    instructions=alice_instructions,
    storage=SqliteStorage(table_name="alice_agent", db_file=agent_storage),
    # Memória simplificada - menos confusão para o LLM
    add_history_to_messages=True,
    num_history_responses=3,  # Reduzido de 10 para 3
    markdown=True,
)

# --- Playground Customizado ---

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

class CustomPlayground(Playground):
    def get_app(self):
        app = super().get_app()
        app.state.agents = {agent.name: agent for agent in self.agents}
        routes_to_keep = [
            route for route in app.routes if getattr(route, "path", "") != "/v1/playground/agents/{agent_id}/runs"
        ]
        app.router.routes = routes_to_keep


        @app.post("/v1/playground/agents/{agent_id}/runs", tags=["Playground"])
        def run_agent_custom(agent_id: str, payload: CustomRunPayload, request: Request):
            agents_dict: Dict[str, Agent] = request.app.state.agents
            agent = agents_dict.get(agent_id)
            if not agent:
                return {"error": f"Agent with ID '{agent_id}' not found."}

            # EXTRAÇÃO CRÍTICA: Quebra payload em variáveis explícitas para garantir uso correto
            current_conversation_id = payload.conversation_id
            current_contact_id = payload.contact_id
            current_user_id = payload.user_id
            current_city = payload.custom_attributes_city
            current_category = payload.custom_attributes_category

            context = {
                "user_id": current_user_id,
                "contact_id": current_contact_id,
                # CORREÇÃO: Usa .model_dump() para ser compatível com Pydantic v2
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
            print(f"[LOG] Contexto recebido no endpoint: {context}")
            print(f"[DEBUG] Variáveis extraídas: conversation_id={current_conversation_id}, contact_id={current_contact_id}")
            print(f"[DEBUG] Validações: CIDADE_JA_INFORMADA={context['CIDADE_JA_INFORMADA']}, CATEGORIA_JA_INFORMADA={context['CATEGORIA_JA_INFORMADA']}")

            result = agent.run(
                message=payload.message,
                session_id=payload.session_id,
                context=context
            )

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
                return to_json_safe(result.dict())
            if hasattr(result, "model_dump"):
                return to_json_safe(result.model_dump())
            if isinstance(result, dict):
                return to_json_safe(result)
            return {"result": to_json_safe(result)}

        @app.get("/health", tags=["Health"])
        def health_check():
            """Health check endpoint for deployment monitoring"""
            return {
                "status": "healthy",
                "agent": "Alice",
                "tools": ["busca_knowledge_base", "suporte", "cadastros", "duvidas", "atribui_a_cidade", "contato_categoria", "busca_duckduckgo"],
                "version": "2.0",
                "features": ["chatwoot_integration", "knowledge_base", "duckduckgo_search", "intelligent_fallback"]
            }

        @app.get("/debug/knowledge", tags=["Debug"])
        def debug_knowledge_base():
            """Debug endpoint para verificar status da base de conhecimento"""
            try:
                storage = SqliteStorage(table_name="knowledge", db_file=agent_storage)
                sessions = storage.get_all_sessions()

                if not sessions:
                    return {
                        "status": "empty",
                        "count": 0,
                        "titles": [],
                        "message": "Base de conhecimento vazia"
                    }

                titles = []
                for session in sessions:
                    if hasattr(session, 'session_data') and session.session_data:
                        title = session.session_data.get("title", "Sem título")
                        titles.append(title)

                return {
                    "status": "populated",
                    "count": len(sessions),
                    "titles": titles,
                    "message": f"Base de conhecimento com {len(sessions)} documentos"
                }

            except Exception as e:
                return {
                    "status": "error",
                    "count": 0,
                    "titles": [],
                    "error": str(e),
                    "message": f"Erro ao acessar base de conhecimento: {e}"
                }

        @app.post("/debug/reload-knowledge", tags=["Debug"])
        def reload_knowledge_base():
            """Força recarregamento da base de conhecimento"""
            try:
                result = ensure_knowledge_base_startup()
                if result:
                    storage = SqliteStorage(table_name="knowledge", db_file=agent_storage)
                    sessions = storage.get_all_sessions()
                    return {
                        "status": "success",
                        "count": len(sessions) if sessions else 0,
                        "message": f"Base de conhecimento recarregada com {len(sessions) if sessions else 0} documentos"
                    }
                else:
                    return {
                        "status": "failed",
                        "count": 0,
                        "message": "Falha ao recarregar base de conhecimento"
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "count": 0,
                    "error": str(e),
                    "message": f"Erro ao recarregar: {e}"
                }

        return app

# --- Inicialização do App ---
playground_app = CustomPlayground(agents=[alice_agent])
app = playground_app.get_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("playground:app", host="0.0.0.0", port=port, reload=False)
