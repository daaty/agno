import os
import requests
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
CHATWOOT_TOKEN = os.getenv("CHATWOOT_API_TOKEN")

class ContatoCategoriaTool:
    name = "contato_categoria"
    description = "Ferramenta para atualizar o atributo 'categoria' de um contato no Chatwoot."
    """
    Ferramenta para atualizar o atributo 'categoria' de um contato no Chatwoot.
    """
    def run(self, input):
        contact_id = input.get("contact_id")
        categoria = input.get("categoria")
        if not contact_id or not categoria:
            return "É necessário informar contact_id e categoria."
        url = f"https://chat.urbanmt.com.br/api/v1/accounts/1/contacts/{contact_id}"
        headers = {
            "api_access_token": CHATWOOT_TOKEN,
            "Content-Type": "application/json"
        }
        body = {"custom_attributes": {"categoria": categoria}}
        response = requests.patch(url, json=body, headers=headers)
        response.raise_for_status()
        return response.json()
        return response.json()
