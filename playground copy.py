import os
from dotenv import load_dotenv
from fastapi import Body, FastAPI, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.playground import Playground
from agno.storage.sqlite import SqliteStorage
from agno.memory.agent import AgentMemory
from agno.memory.db.sqlite import SqliteMemoryDb
from agno.tools.reasoning import ReasoningTools

# Importe suas ferramentas customizadas
from tools.suporte_tool import SuporteTool
from tools.cadastros_tool import CadastrosTool
from tools.duvidas_tool import DuvidasTool
from tools.atribui_cidade_tool import AtribuiCidadeTool
from tools.contato_categoria_tool import ContatoCategoriaTool

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# --- Definição das Ferramentas ---
# Funções wrapper para garantir que as ferramentas sejam registradas corretamente no Agno

def suporte_tool(conversation_id: str):
    """Ferramenta para transferir conversa para o time de suporte no Chatwoot. Requer 'conversation_id'."""
    print(f"[LOG] suporte_tool chamado com conversation_id={conversation_id}")
    assert conversation_id is not None, "conversation_id não pode ser None!"
    return SuporteTool().run({"conversation_id": conversation_id})
suporte_tool.__name__ = "suporte"


def cadastros_tool(conversation_id: str):
    """Ferramenta para transferir conversa para o time de cadastros no Chatwoot. Requer 'conversation_id'."""
    print(f"[LOG] cadastros_tool chamado com conversation_id={conversation_id}")
    assert conversation_id is not None, "conversation_id não pode ser None!"
    return CadastrosTool().run({"conversation_id": conversation_id})
cadastros_tool.__name__ = "cadastros"


def duvidas_tool(conversation_id: str):
    """Ferramenta para transferir conversa para o time de dúvidas gerais no Chatwoot. Requer 'conversation_id'."""
    print(f"[LOG] duvidas_tool chamado com conversation_id={conversation_id}")
    assert conversation_id is not None, "conversation_id não pode ser None!"
    return DuvidasTool().run({"conversation_id": conversation_id})
duvidas_tool.__name__ = "duvidas"

def atribui_cidade_tool(contact_id: str, cidade: str):
    """Ferramenta para atribuir cidade ao contato no Chatwoot. Requer 'contact_id' e 'cidade'."""
    print(f"[LOG] atribui_cidade_tool chamado com contact_id={contact_id}, cidade={cidade}")
    return AtribuiCidadeTool().run({"contact_id": contact_id, "cidade": cidade})
atribui_cidade_tool.__name__ = "atribui_a_cidade"

def contato_categoria_tool(input):
    """Ferramenta para atualizar o atributo 'categoria' de um contato no Chatwoot."""
    return ContatoCategoriaTool().run(input)
contato_categoria_tool.__name__ = "contato_categoria"

# --- Configuração do Agente ---
os.makedirs("tmp", exist_ok=True)
agent_storage = "tmp/agents.db"

# INSTRUÇÕES ATUALIZADAS: Agora o agente sabe que deve procurar dados no contexto.
alice_instructions = [
    # Princípios Fundamentais
    "Você é Alice, assistente virtual da Urban. Seja sempre humana, calorosa, proativa e, acima de tudo, prestativa.",
    "Sempre que possível, responda diretamente usando a base de conhecimento e o contexto atual. Só faça perguntas adicionais se realmente não houver resposta na base de conhecimento ou contexto. Nunca peça confirmação de dados que já estejam presentes no contexto ou na base de conhecimento.",
    "Antes de perguntar qualquer coisa ao usuário, SEMPRE revise o histórico da conversa e as memórias armazenadas. Nunca peça informações (como cidade ou categoria) que já estejam presentes no contexto, histórico ou memórias do usuário. Se a cidade ou categoria já estiverem no contexto ou histórico, NUNCA pergunte novamente, apenas siga o fluxo normalmente.",
    "Se o campo `custom_attributes_category` existir no contexto e não for vazio (qualquer string), considere a categoria já registrada e NUNCA pergunte novamente, nem peça confirmação. Nunca acione a ferramenta de categoria se o campo já estiver presente. Nunca ignore o valor do campo `custom_attributes_category` do contexto. Sempre confie nele, mesmo que pareça estranho ou diferente do esperado.",
    "Nunca acione a ferramenta de categoria se a categoria já estiver presente no contexto. Apenas siga o fluxo normalmente.",
    "Sempre tente responder usando sua base de conhecimento e informações do contexto. Só ofereça transferência para suporte, cadastros ou dúvidas se realmente não souber a resposta ou se o usuário pedir explicitamente.",
    "Se não souber a resposta, pergunte ao usuário se deseja ser transferido para o time competente (suporte, cadastros ou dúvidas). Só acione a ferramenta de transferência após o usuário confirmar que deseja ser transferido.",
    "Ao acionar qualquer ferramenta de transferência (suporte, cadastros, duvidas), utilize EXCLUSIVAMENTE o valor do campo 'conversation_id' presente no contexto ATUAL. NUNCA use qualquer outro valor, mesmo que tenha visto em mensagens anteriores, histórico, memória ou qualquer outro lugar. Apenas use o valor literal do campo 'conversation_id' do contexto recebido nesta mensagem.",
    "Ao acionar as ferramentas de atribuição (atribui_a_cidade, contato_categoria), use sempre os dados do contexto atual (ex: contact_id, cidade, categoria). Nunca tente inferir, buscar em outro lugar ou inventar valores. Nunca use 'undefined' como contact_id. Se não houver contact_id no contexto, informe o usuário e ofereça transferência, mas nunca acione a ferramenta sem o contact_id literal do contexto.",
    "Exemplo de erro a evitar: Não acione a ferramenta contato_categoria com contact_id=undefined. Sempre use o valor literal do campo contact_id do contexto recebido nesta mensagem. Se não houver, não acione a ferramenta e informe o usuário.",
    "Se faltar algum dado essencial (ex: contact_id), informe o usuário que não é possível executar a ação e ofereça transferência para um especialista, mas NÃO tente acionar a ferramenta sem os dados.",
    "Sempre analise o histórico da conversa e os dados de contexto (como contact_id, custom_attributes_city) antes de fazer uma pergunta. O `contact_id` é essencial para usar ferramentas como `atribui_a_cidade`.",
    # (Removido: instrução sobre a ferramenta think. O agente deve usar apenas memória e raciocínio nativos do Agno.)

    # Fluxo de Atendimento Corrigido com Tratamento de Falhas
    "ETAPA 1: Coleta de Dados Essenciais. Seu primeiro objetivo é garantir que você tenha a cidade e a categoria do usuário.",
    "1. Verifique a Cidade: Só pergunte a cidade se o campo `custom_attributes_city` NÃO estiver presente ou estiver vazio no contexto. Se estiver presente e não for vazio (qualquer string), NÃO pergunte novamente.",
    "2. Verifique a Categoria: Só pergunte a categoria se o campo `custom_attributes_category` NÃO estiver presente ou estiver vazio no contexto. Se estiver presente e não for vazio (qualquer string), NÃO pergunte novamente.",
    "Exemplo de contexto recebido: {'custom_attributes_city': 'Colider', ...}. Se o campo `custom_attributes_city` existir e não for vazio, considere a cidade já registrada e NÃO pergunte novamente, mesmo que o valor seja qualquer string.",
    "Exemplo de contexto recebido: {'custom_attributes_category': 'Motorista', ...}. Se o campo `custom_attributes_category` existir e não for vazio, considere a categoria já registrada e NÃO pergunte novamente, mesmo que o valor seja qualquer string.",
    "Nunca ignore o valor do campo `custom_attributes_city` do contexto. Sempre confie nele, mesmo que pareça estranho ou diferente do esperado.",
    "2. Use a Ferramenta `atribui_a_cidade`: Assim que o usuário responder, tente usar a ferramenta `atribui_a_cidade`. Para isso, você PRECISA do `contact_id` (que deve estar no contexto) e da `cidade`.",
    "   - Se a ferramenta for executada com sucesso, confirme ao usuário: 'Obrigada! Cidade registrada.' e passe para o próximo passo.",
    "   - Se a ferramenta FALHAR por falta do `contact_id`, você NÃO DEVE perguntar a cidade novamente. Informe o problema: 'Puxa, não consegui identificar seu contato para salvar a cidade. Vou te transferir para um especialista para resolver isso, tudo bem?'.",
    "3. Verifique a Categoria: Depois de ter a cidade, verifique a categoria (`custom_attributes_category`) e colete se necessário.",
    "4. Prossiga: Somente quando tiver confirmado tanto a cidade quanto a categoria, você pode prosseguir para a ETAPA 2.",
]

alice_agent = Agent(
    name="Alice",
    model=OpenAIChat(id="gpt-4o-mini", api_key=api_key),
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
        num_history_runs=10,
    ),
    knowledge=True,
    markdown=True,
    enable_agentic_memory=True,
    enable_session_summaries=True,
    # O raciocínio e memória agora são nativos do Agno, sem ReasoningTools ou think.
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

        return app

# --- Inicialização do App ---
playground_app = CustomPlayground(agents=[alice_agent])
app = playground_app.get_app()

if __name__ == "__main__":
    playground_app.serve("playground:app", reload=True)
