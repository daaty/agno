import os
import requests
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
CHATWOOT_TOKEN = os.getenv("CHATWOOT_API_TOKEN")

class DuvidasTool:
    name = "duvidas"
    description = "Ferramenta para transferir conversa para o time de dúvidas gerais no Chatwoot."
    """
    Ferramenta para transferir conversa para o time de dúvidas gerais no Chatwoot.
    """
    def run(self, input):
        conversation_id = input.get("conversation_id")
        if not conversation_id:
            return "É necessário informar conversation_id."
        url = f"https://chat.urbanmt.com.br/api/v1/accounts/1/conversations/{conversation_id}/assignments"
        headers = {
            "Content-Type": "application/json",
            "api_access_token": CHATWOOT_TOKEN  # Correção: usar api_access_token em vez de Authorization Bearer
        }
        body = {"team_id": 3}
        logger.debug(f"[{self.__class__.__name__}] POST para: {url}")
        # Headers logados apenas em debug se necessário
        logger.debug(f"[{self.__class__.__name__}] Body: {body}")
        response = requests.post(url, json=body, headers=headers)
        logger.info(f"[{self.__class__.__name__}] Status: {response.status_code}")
        if response.status_code != 200: logger.error(f"[{self.__class__.__name__}] Erro: {response.text}")
        response.raise_for_status()
        return response.json()
