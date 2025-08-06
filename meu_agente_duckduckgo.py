from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=Gemini(id="gemini-2.0-flash"),
    tools=[DuckDuckGoTools()],
    instructions="Pesquise na web usando DuckDuckGo e responda sempre em português.",
    markdown=True,
)

agent.print_response("Quais as últimas notícias sobre inteligência artificial?")
