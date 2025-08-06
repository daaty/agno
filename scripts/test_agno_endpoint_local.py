import requests

url = "http://localhost:7777/v1/agents/alice/runs"
payload = {
    "mensagem": "Quero cadastrar minha cidade",
    "user_id": "123",
    "contact_id": "456",
    "cidade": "Guarantã do Norte",
    "categoria": "motorista"
}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"Status code: {response.status_code}")
    print("Resposta:")
    print(response.text)
except Exception as e:
    print(f"Erro ao testar o endpoint: {e}")
