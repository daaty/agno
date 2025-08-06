from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.playground import Playground
from agno.storage.sqlite import SqliteStorage
from agno.tools.duckduckgo import DuckDuckGoTools
import os

# Cria diretório para o banco de dados se não existir
os.makedirs("tmp", exist_ok=True)
agent_storage = "tmp/agents_lmstudio.db"

# Configure o modelo para usar LM Studio local
# Altere o id para o nome do modelo carregado no LM Studio (ex: "phi3", "llama3", etc)
# api_base deve ser o endpoint HTTP do LM Studio (ex: http://localhost:1234/v1)
web_agent = Agent(
    name="Web Agent",
    model=OpenAIChat(
        id="phi3",  # troque para o modelo desejado
        api_base="http://localhost:1234/v1",  # endpoint LM Studio local
        api_key="sk-local"  # LM Studio normalmente não exige autenticação
    ),
    tools=[DuckDuckGoTools()],
    instructions=["Sempre inclua fontes nas respostas."],
    storage=SqliteStorage(table_name="web_agent_lmstudio", db_file=agent_storage),
    add_datetime_to_instructions=True,
    add_history_to_messages=True,
    num_history_responses=5,
    markdown=True,
)

playground_app = Playground(agents=[web_agent])
app = playground_app.get_app()

if __name__ == "__main__":
    playground_app.serve("playground:app", reload=True)
