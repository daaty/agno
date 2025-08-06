from agno.agent import Agent
from agno.models.google import Gemini
from agno.playground import Playground
from agno.storage.sqlite import SqliteStorage
from agno.tools.reasoning import ReasoningTools
import os

# Cria diretório para o banco de dados se não existir
os.makedirs("tmp", exist_ok=True)
agent_storage = "tmp/agents_vendas.db"

web_agent = Agent(
    name="Valdefino - Vendas Diabetes",
    model=Gemini(id="gemini-2.0-flash", api_key="SUA_API_KEY"),
    tools=[ReasoningTools(add_instructions=True)],
    instructions="Você é o agente de vendas Valdefino, especialista em tratamentos para diabetes. Siga o funil de vendas, trate objeções, colete dados e registre tudo. Use reasoning para planejar e justificar decisões.",
    storage=SqliteStorage(table_name="vendas_agent", db_file=agent_storage),
    markdown=True,
)

playground_app = Playground(agents=[web_agent])
app = playground_app.get_app()

if __name__ == "__main__":
    playground_app.serve("playground:app", reload=True)
