import requests

url = "http://localhost:8000/v1/playground/agents/Alice/runs"
payload = {
    "message": "O que é EAR na habilitação?",
    "session_id": "teste1"
}
resp = requests.post(url, json=payload)
print(resp.status_code)
print(resp.json())
