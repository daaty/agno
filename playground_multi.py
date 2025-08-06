from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.openai import OpenAIChat
from agno.playground import Playground
from agno.storage.sqlite import SqliteStorage
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.reasoning import ReasoningTools
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from atribui_cidade_tool import AtribuiCidadeTool

os.makedirs("tmp", exist_ok=True)

agent_storage = "tmp/agents.db"
agent_storage_vendas = "tmp/agents_vendas.db"
agent_storage_lmstudio = "tmp/agents_lmstudio.db"

web_agent = Agent(
    name="Web Agent",
    model=Gemini(id="gemini-2.0-flash", api_key="SUA_API_KEY"),
    tools=[DuckDuckGoTools()],
    instructions=["Sempre inclua fontes nas respostas."],
    storage=SqliteStorage(table_name="web_agent", db_file=agent_storage),
    markdown=True,
)

vendas_agent = Agent(
    name="Valdefino - Vendas Diabetes",
    model=Gemini(id="gemini-2.0-flash", api_key="SUA_API_KEY"),
    tools=[ReasoningTools(add_instructions=True)],
    instructions="Você é o agente de vendas Valdefino, especialista em tratamentos para diabetes. Siga o funil de vendas, trate objeções, colete dados e registre tudo. Use reasoning para planejar e justificar decisões.",
    storage=SqliteStorage(table_name="vendas_agent", db_file=agent_storage_vendas),
    markdown=True,
)

lmstudio_agent = Agent(
    name="Agente DuckDuckGo + Chatwoot",
    model=OpenAIChat(
        id="mistral-7b-instruct-v0.2",
        base_url="http://localhost:1234/v1",
        api_key="sk-local"
    ),
    tools=[DuckDuckGoTools(), AtribuiCidadeTool()],
    instructions=(
        "Pesquise na web usando DuckDuckGo e responda sempre em português. "
        "Ferramentas disponíveis:\n"
        "1. duckduckgo_search: pesquisa na web.\n"
        "2. duckduckgo_news: últimas notícias.\n"
        "3. atribuir cidade: atualiza o atributo 'cidade' de um contato no Chatwoot. "
        "Para usar, forneça o comando 'atribuir cidade <contact_id> <cidade>'. "
        "Use a ferramenta de atribuição de cidade apenas quando o usuário informar uma cidade válida e um contact_id."
    ),
    storage=SqliteStorage(table_name="web_agent_lmstudio", db_file=agent_storage_lmstudio),
    markdown=True,
)

playground_app = Playground(agents=[web_agent, vendas_agent, lmstudio_agent])
app = playground_app.get_app()

if __name__ == "__main__":
    playground_app.serve("playground:app", reload=True)
