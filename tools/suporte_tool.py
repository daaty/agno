import os
import requests
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
CHATWOOT_TOKEN = os.getenv("CHATWOOT_API_TOKEN")

class SuporteTool:
    name = "suporte"
    description = "Ferramenta para transferir conversa para o time de suporte no Chatwoot."
    """
    Ferramenta para transferir conversa para o time de suporte no Chatwoot.
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
        body = {"team_id": 1}
        logger.info(f"[SuporteTool] Transferindo conversa {conversation_id} para suporte")
        logger.debug(f"[SuporteTool] POST para: {url}")
        logger.debug(f"[SuporteTool] Body: {body}")
        response = requests.post(url, json=body, headers=headers)
        logger.info(f"[SuporteTool] Status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"[SuporteTool] Erro na resposta: {response.text}")
        response.raise_for_status()
        return response.json()
