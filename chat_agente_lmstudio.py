from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from atribui_cidade_tool import AtribuiCidadeTool

# Configure o agente para usar LM Studio local
# Troque o id para o nome do modelo carregado no LM Studio (ex: "mistral-7b-instruct-v0.2")
agent = Agent(
    model=OpenAIChat(
        id="mistral-7b-instruct-v0.2",  # nome do modelo carregado
        base_url="http://localhost:1234/v1",  # endpoint LM Studio local
        api_key="sk-local"  # LM Studio normalmente não exige autenticação
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
