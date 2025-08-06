import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.playground import Playground
from agno.storage.sqlite import SqliteStorage
from agno.memory.agent import AgentMemory
from agno.memory.db.sqlite import SqliteMemoryDb
from agno.knowledge.text import TextKnowledgeBase

# Importe suas ferramentas customizadas
from tools.suporte_tool import SuporteTool
from tools.cadastros_tool import CadastrosTool
from tools.duvidas_tool import DuvidasTool
from tools.atribui_cidade_tool import AtribuiCidadeTool
from tools.contato_categoria_tool import ContatoCategoriaTool

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
chatwoot_token = os.getenv("CHATWOOT_API_TOKEN")

if not api_key:
    raise ValueError("OPENAI_API_KEY não encontrada no arquivo .env")
if not chatwoot_token:
    raise ValueError("CHATWOOT_API_TOKEN não encontrada no arquivo .env")

# --- VALIDAÇÃO CENTRALIZADA ---
def validate_conversation_id(conversation_id: str) -> bool:
    """Valida se o conversation_id é válido"""
    return conversation_id and conversation_id.isdigit() and 1 <= len(conversation_id) <= 6

def validate_contact_id(contact_id: str) -> bool:
    """Valida se o contact_id é válido"""
    return contact_id and contact_id.isdigit() and contact_id != "undefined"

# --- FERRAMENTAS OTIMIZADAS ---
def suporte_tool(conversation_id: str):
    """Transferir conversa para o time de suporte no Chatwoot"""
    if not validate_conversation_id(conversation_id):
        return {"error": f"conversation_id inválido: {conversation_id}"}

    try:
        result = SuporteTool().run({"conversation_id": conversation_id})
        return {"success": True, "message": "Transferido para suporte", "data": result}
    except Exception as e:
        return {"error": f"Erro ao transferir: {str(e)}"}

def cadastros_tool(conversation_id: str):
    """Transferir conversa para o time de cadastros no Chatwoot"""
    if not validate_conversation_id(conversation_id):
        return {"error": f"conversation_id inválido: {conversation_id}"}

    try:
        result = CadastrosTool().run({"conversation_id": conversation_id})
        return {"success": True, "message": "Transferido para cadastros", "data": result}
    except Exception as e:
        return {"error": f"Erro ao transferir: {str(e)}"}

def duvidas_tool(conversation_id: str):
    """Transferir conversa para o time de dúvidas no Chatwoot"""
    if not validate_conversation_id(conversation_id):
        return {"error": f"conversation_id inválido: {conversation_id}"}

    try:
        result = DuvidasTool().run({"conversation_id": conversation_id})
        return {"success": True, "message": "Transferido para dúvidas", "data": result}
    except Exception as e:
        return {"error": f"Erro ao transferir: {str(e)}"}

def atribui_cidade_tool(contact_id: str, cidade: str):
    """Atribuir cidade ao contato no Chatwoot"""
    if not validate_contact_id(contact_id):
        return {"error": f"contact_id inválido: {contact_id}"}

    if not cidade or len(cidade.strip()) < 2:
        return {"error": "Cidade inválida"}

    try:
        result = AtribuiCidadeTool().run({"contact_id": contact_id, "cidade": cidade})
        return {"success": True, "message": f"Cidade '{cidade}' atribuída com sucesso", "data": result}
    except Exception as e:
        return {"error": f"Erro ao atribuir cidade: {str(e)}"}

def contato_categoria_tool(contact_id: str, categoria: str):
    """Atualizar categoria do contato no Chatwoot"""
    if not validate_contact_id(contact_id):
        return {"error": f"contact_id inválido: {contact_id}"}

    if not categoria or len(categoria.strip()) < 2:
        return {"error": "Categoria inválida"}

    try:
        result = ContatoCategoriaTool().run({"contact_id": contact_id, "categoria": categoria})
        return {"success": True, "message": f"Categoria '{categoria}' atribuída com sucesso", "data": result}
    except Exception as e:
        return {"error": f"Erro ao atribuir categoria: {str(e)}"}

# --- CONFIGURAÇÃO DO AGENTE OTIMIZADA ---
os.makedirs("tmp", exist_ok=True)
agent_storage = "tmp/agents.db"

# BASE DE CONHECIMENTO
knowledge_base = TextKnowledgeBase(
    sources=[
        """
        URBAN - ASSISTENTE VIRTUAL PARA MOTORISTAS

        PROCESSO DE CADASTRO:
        1. Coletar cidade do usuário (obrigatório)
        2. Coletar categoria: Motorista, Entregador, ou Taxista (obrigatório)
        3. Fornecer informações sobre requisitos e documentação
        4. Orientar sobre próximos passos

        CATEGORIAS DISPONÍVEIS:
        - Motorista: Transporte de passageiros via aplicativo
        - Entregador: Entrega de produtos e comidas
        - Taxista: Serviço de táxi tradicional

        TRANSFERÊNCIAS:
        - Suporte: Problemas técnicos, bugs, falhas no app
        - Cadastros: Documentação, aprovação, rejeição de cadastro
        - Dúvidas: Informações gerais, como funciona, valores

        IMPORTANTE: Sempre confirme cidade e categoria antes de prosseguir.
        """
    ]
)

# INSTRUÇÕES SIMPLIFICADAS E EFICAZES
alice_instructions = [
    "Você é Alice, assistente virtual da Urban. Seja calorosa, proativa e eficiente.",

    "REGRA FUNDAMENTAL: Use sempre os dados exatos do contexto atual. Nunca invente, infira ou use dados de outras conversas.",

    "FLUXO PRINCIPAL:",
    "1. Verifique se cidade e categoria já estão no contexto (custom_attributes_city e custom_attributes_category)",
    "2. Se estiverem presentes e não vazios, NUNCA pergunte novamente - prossiga diretamente",
    "3. Se faltarem, colete apenas os dados ausentes",
    "4. Use as ferramentas apenas quando necessário e com os dados exatos do contexto",

    "TRANSFERÊNCIAS: Só ofereça após confirmar que não pode ajudar com sua base de conhecimento",

    "DADOS OBRIGATÓRIOS:",
    "- conversation_id: Use exatamente o valor do contexto atual para transferências",
    "- contact_id: Use exatamente o valor do contexto atual para atribuições",

    "Se algum dado obrigatório estiver ausente ou inválido, informe o usuário e ofereça transferência para especialista."
]

alice_agent = Agent(
    name="Alice",
    model=OpenAIChat(id="gpt-4o", api_key=api_key),  # Modelo mais robusto
    tools=[
        suporte_tool,
        cadastros_tool,
        duvidas_tool,
        atribui_cidade_tool,
        contato_categoria_tool
    ],
    instructions=alice_instructions,
    storage=SqliteStorage(table_name="alice_agent", db_file=agent_storage),
    memory=AgentMemory(
        db=SqliteMemoryDb(table_name="alice_memory", db_file=agent_storage),
        create_user_memories=True,
        update_user_memories_after_run=True,
        create_session_summary=True,
        update_session_summary_after_run=True,
        add_history_to_messages=True,
        num_history_runs=20,  # Aumentado para melhor contexto
    ),
    knowledge=knowledge_base,
    markdown=True,
    show_tool_calls=True,  # Para debug
    debug_mode=True,  # Para melhor debugging
)

# --- PAYLOAD OTIMIZADO ---
class EmotionData(BaseModel):
    emocao_primaria: Optional[str] = None
    sentimento: Optional[str] = None
    justificativa: Optional[str] = None

class OptimizedRunPayload(BaseModel):
    message: str = Field(..., min_length=1, description="Mensagem do usuário")
    session_id: str = Field(..., min_length=1, description="ID da sessão")
    user_id: Optional[str] = None
    contact_id: Optional[str] = None
    dados_emocao: Optional[EmotionData] = Field(None, alias="dados_emocao")
    conversation_id: Optional[str] = None
    custom_attributes_city: Optional[str] = None
    custom_attributes_category: Optional[str] = None

    @validator('conversation_id')
    def validate_conversation_id(cls, v):
        if v and not validate_conversation_id(v):
            raise ValueError('conversation_id inválido')
        return v

    @validator('contact_id')
    def validate_contact_id(cls, v):
        if v and not validate_contact_id(v):
            raise ValueError('contact_id inválido')
        return v

# --- PLAYGROUND OTIMIZADO ---
class OptimizedPlayground(Playground):
    def get_app(self):
        app = super().get_app()
        app.state.agents = {agent.name: agent for agent in self.agents}

        # Remove rota padrão
        routes_to_keep = [
            route for route in app.routes
            if getattr(route, "path", "") != "/v1/playground/agents/{agent_id}/runs"
        ]
        app.router.routes = routes_to_keep

        @app.post("/v1/playground/agents/{agent_id}/runs", tags=["Playground"])
        async def run_agent_optimized(agent_id: str, payload: OptimizedRunPayload, request: Request):
            try:
                agents_dict: Dict[str, Agent] = request.app.state.agents
                agent = agents_dict.get(agent_id)

                if not agent:
                    raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' não encontrado")

                # Contexto validado e limpo
                context = {
                    "user_id": payload.user_id,
                    "contact_id": payload.contact_id,
                    "dados_emocao": payload.dados_emocao.model_dump() if payload.dados_emocao else None,
                    "conversation_id": payload.conversation_id,
                    "custom_attributes_city": payload.custom_attributes_city,
                    "custom_attributes_category": payload.custom_attributes_category,
                }

                # Remove valores None para contexto mais limpo
                context = {k: v for k, v in context.items() if v is not None}

                print(f"[CONTEXTO] {context}")

                # Executa o agente
                result = agent.run(
                    message=payload.message,
                    session_id=payload.session_id,
                    context=context
                )

                # Processamento de resposta otimizado
                if hasattr(result, 'model_dump'):
                    return result.model_dump()
                elif hasattr(result, 'dict'):
                    return result.dict()
                elif isinstance(result, dict):
                    return result
                else:
                    return {"response": str(result)}

            except Exception as e:
                print(f"[ERRO] {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        return app

# --- INICIALIZAÇÃO ---
playground_app = OptimizedPlayground(agents=[alice_agent])
app = playground_app.get_app()

if __name__ == "__main__":
    print("🚀 Iniciando Alice otimizada...")
    playground_app.serve("playground_optimized:app", reload=True)
