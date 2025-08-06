import os
import requests
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
CHATWOOT_TOKEN = os.getenv("CHATWOOT_API_TOKEN")

class AtribuiCidadeTool:
    name = "atribui_a_cidade"
    description = "Ferramenta para atribuir cidade ao contato no Chatwoot."
    def run(self, input):
        # Espera input como dict: {"contact_id": "...", "cidade": "..."}
        contact_id = input.get("contact_id")
        cidade = input.get("cidade")
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
        try:
            response = requests.patch(url, json=body, headers=headers)
            if response.status_code == 200:
                return f"Cidade '{cidade}' atribuída com sucesso ao contato {contact_id}."
            else:
                return f"Erro ao atribuir cidade: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Erro na requisição: {str(e)}"
