import os
import logging
from dotenv import load_dotenv
from fastapi import Body, FastAPI, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.playground import Playground
from agno.storage.sqlite import SqliteStorage

# Configurar logging diretamente aqui para evitar problemas de importação
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    logger.info(f"[SuporteTool] Chamado com conversation_id={conversation_id}")
    logger.debug(f"[SuporteTool] Valor recebido: '{conversation_id}' (tipo: {type(conversation_id)})")
    assert conversation_id is not None, "conversation_id não pode ser None!"

    # VALIDAÇÃO CRÍTICA: Bloqueia IDs que não são strings numéricas simples (evita IDs longos incorretos)
    if not conversation_id.isdigit() or len(conversation_id) > 6:
        logger.error(f"[SuporteTool] conversation_id inválido: {conversation_id}. Bloqueando chamada.")
        logger.info("[SuporteTool] Dica: Use EXATAMENTE o conversation_id do contexto, como '107'.")
        return {"error": f"conversation_id inválido: {conversation_id}. Use o valor LITERAL do contexto: '107'."}

    return SuporteTool().run({"conversation_id": conversation_id})
# suporte_tool.__name__ = "suporte"  # Comentado para debug


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
# cadastros_tool.__name__ = "cadastros"  # Comentado para debug


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
# duvidas_tool.__name__ = "duvidas"  # Comentado para debug

def atribui_cidade_tool(contact_id: str, cidade: str):
    """Ferramenta para atribuir cidade ao contato no Chatwoot. Requer 'contact_id' e 'cidade'."""
    print(f"[LOG] atribui_cidade_tool chamado com contact_id={contact_id}, cidade={cidade}")

    # VALIDAÇÃO CRÍTICA: Bloqueia contact_id inválidos como 'undefined'
    if contact_id == "undefined" or not contact_id or not contact_id.isdigit():
        print(f"[ERRO] contact_id inválido: {contact_id}. Bloqueando chamada.")
        return {"error": f"contact_id inválido: {contact_id}. Use apenas o ID do contexto atual."}

    return AtribuiCidadeTool().run({"contact_id": contact_id, "cidade": cidade})
# atribui_cidade_tool.__name__ = "atribui_a_cidade"  # Comentado para debug

def contato_categoria_tool(input):
    """Ferramenta para atualizar o atributo 'categoria' de um contato no Chatwoot."""
    return ContatoCategoriaTool().run(input)
# contato_categoria_tool.__name__ = "contato_categoria"  # Comentado para debug

def busca_duckduckgo_tool(query: str):
    """
    Ferramenta de busca DuckDuckGo para informações complementares.

    Use quando:
    - A base de conhecimento não tiver a resposta
    - Usuário perguntar sobre horários de transporte, localizações específicas
    - Problemas técnicos que precisam de soluções atualizadas
    - Informações sobre cidades específicas da região
    """
    logger.info(f"[BuscaDuckDuckGo] Chamado com query={query}")
    return duckduckgo_search(query)
# busca_duckduckgo_tool.__name__ = "busca_duckduckgo"  # Comentado para debug

# --- Configuração do Agente ---
os.makedirs("tmp", exist_ok=True)
agent_storage = "tmp/agents.db"

# INSTRUÇÕES SIMPLIFICADAS: Concisas e diretas como no n8n
alice_instructions = [
    "Você é Alice, assistente virtual da Urban. Seja humana, calorosa e prestativa.",
    "SEMPRE use dados do contexto atual PRIMEIRO. Nunca pergunte informações já presentes no contexto.",
    "CIDADE: Se `custom_attributes_city` existir no contexto, NUNCA pergunte ou acione `atribui_a_cidade`.",
    "CATEGORIA: Se `custom_attributes_category` existir no contexto, NUNCA pergunte ou acione `contato_categoria`.",
    "BUSCA INTELIGENTE: Se não souber responder, use `busca_duckduckgo` para horários de transporte, localizações, problemas técnicos ou informações sobre cidades antes de transferir.",
    "CRÍTICO: Para ferramentas de transferência, use o valor EXATO de conversation_id do contexto. Se o contexto mostra 'conversation_id': '107', use EXATAMENTE '107'. NUNCA use 'current_conversation_id' ou qualquer variável.",
    "CRÍTICO: Para ferramentas de atribuição, use o valor EXATO de contact_id do contexto. Se o contexto mostra 'contact_id': '10', use EXATAMENTE '10'.",
    "Responda diretamente usando conhecimento quando possível. Use busca_duckduckgo como segunda opção. Só ofereça transferência como último recurso.",
]

alice_agent = Agent(
    name="Alice",
    model=OpenAIChat(id="gpt-4o", api_key=api_key),  # Mudança para gpt-4o padrão do Agno
    tools=[
        suporte_tool,
        cadastros_tool,
        duvidas_tool,
        atribui_cidade_tool,
        contato_categoria_tool,
        busca_duckduckgo_tool
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
            logger.info(f"[Alice] Contexto recebido no endpoint: {context}")
            alice_agent.add_context(context)

            result = alice_agent.run(
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
                "tools": ["suporte", "cadastros", "duvidas", "atribui_a_cidade", "contato_categoria", "busca_duckduckgo"],
                "version": "2.0",
                "features": ["chatwoot_integration", "duckduckgo_search", "intelligent_fallback"]
            }

        return app

# --- Inicialização do App ---
playground_app = CustomPlayground(agents=[alice_agent])
app = playground_app.get_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("playground:app", host="0.0.0.0", port=port, reload=False)
