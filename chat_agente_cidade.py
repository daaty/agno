from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.atribui_cidade_tool import AtribuiCidadeTool

agent = Agent(
    model=Gemini(id="gemini-2.0-flash"),
    tools=[DuckDuckGoTools(), AtribuiCidadeTool()],
    instructions="Pesquise na web usando DuckDuckGo e responda sempre em português. Use a ferramenta de atribuição de cidade apenas quando o usuário informar uma cidade válida e um contact_id.",
    markdown=True,
)

while True:
    pergunta = input("Digite sua pergunta (ou 'sair' para encerrar): ")
    if pergunta.lower() == "sair":
        break
    # Exemplo de uso da ferramenta personalizada
    if pergunta.lower().startswith("atribuir cidade"):
        # Espera formato: atribuir cidade <contact_id> <cidade>
        partes = pergunta.split()
        if len(partes) >= 4:
            contact_id = partes[2]
            cidade = " ".join(partes[3:])
            resposta = agent.tools[1].run({"contact_id": contact_id, "cidade": cidade})
            print(resposta)
        else:
            print("Formato: atribuir cidade <contact_id> <cidade>")
    else:
        agent.print_response(pergunta)
