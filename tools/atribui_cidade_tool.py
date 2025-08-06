import os
import requests
from dotenv import load_dotenv

load_dotenv()
CHATWOOT_TOKEN = os.getenv("CHATWOOT_API_TOKEN")

class AtribuiCidadeTool:
    name = "atribui_a_cidade"
    description = "Ferramenta para atribuir cidade ao contato no Chatwoot."
    def run(self, input):
        # Espera input como dict: {"contact_id": "...", "cidade": "..."}
        contact_id = input.get("contact_id")
        cidade = input.get("cidade")

        print(f"[DEBUG] AtribuiCidadeTool executando com contact_id={contact_id}, cidade={cidade}")

        if not contact_id or not cidade:
            return "É necessário informar contact_id e cidade."

        url = f"https://chat.urbanmt.com.br/api/v1/accounts/1/contacts/{contact_id}"
        headers = {
            "api_access_token": CHATWOOT_TOKEN,
            "Content-Type": "application/json"
        }
        body = {
            "custom_attributes": {
                "cidade": cidade
            }
        }

        print(f"[DEBUG] Fazendo PATCH para: {url}")
        print(f"[DEBUG] Headers: {headers}")
        print(f"[DEBUG] Body: {body}")

        try:
            response = requests.patch(url, json=body, headers=headers)
            print(f"[DEBUG] Status code: {response.status_code}")
            print(f"[DEBUG] Response: {response.text}")

            if response.status_code == 200:
                return f"Cidade '{cidade}' atribuída com sucesso ao contato {contact_id}."
            else:
                return f"Erro ao atribuir cidade: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Erro na requisição: {str(e)}"
