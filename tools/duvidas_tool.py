import os
import requests
from dotenv import load_dotenv

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
        print(f"[DEBUG] Fazendo POST para: {url}")
        print(f"[DEBUG] Headers: {headers}")
        print(f"[DEBUG] Body: {body}")
        response = requests.post(url, json=body, headers=headers)
        print(f"[DEBUG] Status code: {response.status_code}")
        print(f"[DEBUG] Response: {response.text}")
        response.raise_for_status()
        return response.json()
