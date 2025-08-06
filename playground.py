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
        print(f"[DICA] O contexto atual tem 'conversation_id': '107'. Use EXATAMENTE '107', não variáveis como 'current_conversation_id'.")
        return {"error": f"conversation_id inválido: {conversation_id}. Use o valor LITERAL do contexto: '107'."}

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
        print(f"[DICA] O contexto atual tem 'conversation_id': '107'. Use EXATAMENTE '107', não variáveis como 'current_conversation_id'.")
        return {"error": f"conversation_id inválido: {conversation_id}. Use o valor LITERAL do contexto: '107'."}

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
        print(f"[DICA] O contexto atual tem 'conversation_id': '107'. Use EXATAMENTE '107', não variáveis como 'current_conversation_id'.")
        return {"error": f"conversation_id inválido: {conversation_id}. Use o valor LITERAL do contexto: '107'."}

    return DuvidasTool().run({"conversation_id": conversation_id})
duvidas_tool.__name__ = "duvidas"

def atribui_cidade_tool(contact_id: str, cidade: str):
    """Ferramenta para atribuir cidade ao contato no Chatwoot. Requer 'contact_id' e 'cidade'."""
    print(f"[LOG] atribui_cidade_tool chamado com contact_id={contact_id}, cidade={cidade}")

    # VALIDAÇÃO CRÍTICA: Bloqueia contact_id inválidos como 'undefined'
    if contact_id == "undefined" or not contact_id or not contact_id.isdigit():
        print(f"[ERRO] contact_id inválido: {contact_id}. Bloqueando chamada.")
        return {"error": f"contact_id inválido: {contact_id}. Use apenas o ID do contexto atual."}

    return AtribuiCidadeTool().run({"contact_id": contact_id, "cidade": cidade})
atribui_cidade_tool.__name__ = "atribui_a_cidade"

def contato_categoria_tool(input):
    """Ferramenta para atualizar o atributo 'categoria' de um contato no Chatwoot."""
    return ContatoCategoriaTool().run(input)
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

        # Usa o método get_all_sessions do SqliteStorage
        all_sessions = storage.get_all_sessions()

        # Filtra resultados que contenham a query no título ou conteúdo
        matches = []
        for session in all_sessions:
            if hasattr(session, 'session_data') and session.session_data:
                session_data = session.session_data
                title = session_data.get("title", "").lower()
                content = session_data.get("content", "").lower()

                if query_lower in title or query_lower in content:
                    matches.append({
                        "title": session_data.get("title", ""),
                        "content": session_data.get("content", "")
                    })

        if matches:
            print(f"[LOG] Encontrados {len(matches)} resultados na knowledge base")
            # Retorna o primeiro resultado mais relevante
            return {
                "found": True,
                "source": "knowledge_base",
                "title": matches[0]["title"],
                "content": matches[0]["content"]
            }
        else:
            print(f"[LOG] Nenhum resultado encontrado na knowledge base para: {query}")
            return {
                "found": False,
                "message": "Informação não encontrada na base de conhecimento local"
            }

    except Exception as e:
        print(f"[ERRO] Erro ao buscar na knowledge base: {e}")
        return {
            "found": False,
            "error": f"Erro na busca local: {str(e)}"
        }

busca_knowledge_base_tool.__name__ = "busca_knowledge_base"# INSTRUÇÕES SIMPLIFICADAS: Concisas e diretas como no n8n
alice_instructions = [
    "Você é Alice, assistente virtual da Urban. Seja humana, calorosa e prestativa.",
    "SEMPRE use dados do contexto atual PRIMEIRO. Nunca pergunte informações já presentes no contexto.",
    "CIDADE: Se `custom_attributes_city` existir no contexto, NUNCA pergunte ou acione `atribui_a_cidade`.",
    "CATEGORIA: Se `custom_attributes_category` existir no contexto, NUNCA pergunte ou acione `contato_categoria`.",
    "CONHECIMENTO: SEMPRE consulte PRIMEIRO a base de conhecimento local usando `busca_knowledge_base` antes de qualquer outra ferramenta.",
    "BUSCA INTELIGENTE: Se a base local não tiver a resposta, use `busca_duckduckgo` para horários de transporte, localizações, problemas técnicos ou informações sobre cidades.",
    "CRÍTICO: Para ferramentas de transferência, use o valor EXATO de conversation_id do contexto. Se o contexto mostra 'conversation_id': '107', use EXATAMENTE '107'. NUNCA use 'current_conversation_id' ou qualquer variável.",
    "CRÍTICO: Para ferramentas de atribuição, use o valor EXATO de contact_id do contexto. Se o contexto mostra 'contact_id': '10', use EXATAMENTE '10'.",
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

            context = {
                "user_id": payload.user_id,
                "contact_id": payload.contact_id,
                # CORREÇÃO: Usa .model_dump() para ser compatível com Pydantic v2
                "dados_emocao": payload.dados_emocao.model_dump() if payload.dados_emocao else None,
                "conversation_id": payload.conversation_id,
                "custom_attributes_city": payload.custom_attributes_city,
                "custom_attributes_category": payload.custom_attributes_category,
            }
            print(f"[LOG] Contexto recebido no endpoint: {context}")

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

        return app

# --- Inicialização do App ---
playground_app = CustomPlayground(agents=[alice_agent])
app = playground_app.get_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("playground:app", host="0.0.0.0", port=port, reload=False)
