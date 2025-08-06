# 🚀 Deploy da Alice (Agente Urban) no EasyPanel

## 📋 Pré-requisitos

- Conta no EasyPanel
- Repositório Git configurado
- Variáveis de ambiente configuradas

## ⚙️ Configuração no EasyPanel

### 1. **Configuração do Projeto:**
- **Build Command**: Automático (Heroku Buildpack)
- **Start Command**: `web: uvicorn playground:app --host 0.0.0.0 --port $PORT`
- **Buildpack**: `heroku/builder:24`

### 2. **Variáveis de Ambiente Obrigatórias:**

```env
OPENAI_API_KEY=sua_openai_api_key_aqui
CHATWOOT_API_TOKEN=seu_chatwoot_token_aqui
```

### 3. **Variáveis Opcionais:**

```env
GEMINI_API_KEY=sua_gemini_api_key_aqui
PORT=8000
```

## 🔧 Arquivos de Deploy

- **`Procfile`**: Define como iniciar a aplicação
- **`requirements.txt`**: Lista todas as dependências
- **`runtime.txt`**: Especifica versão do Python (3.11.7)

## 🎯 Endpoints Disponíveis

### **Playground Padrão:**
```
POST /v1/playground/agents/Alice/runs
Content-Type: application/json

{
  "message": "Sua mensagem aqui",
  "session_id": "user_123",
  "user_id": "optional",
  "contact_id": "123",
  "conversation_id": "107",
  "custom_attributes_city": "Sinop",
  "custom_attributes_category": "Passageiro",
  "dados_emocao": {
    "emocao_primaria": "Neutro",
    "sentimento": "Positivo"
  }
}
```

### **Health Check:**
```
GET /health
```

## 🛠️ Ferramentas Disponíveis

1. **suporte** - Transferir para time de suporte (team_id: 1)
2. **cadastros** - Transferir para time de cadastros (team_id: 2)
3. **duvidas** - Transferir para time de dúvidas (team_id: 3)
4. **atribui_a_cidade** - Atribuir cidade ao contato
5. **contato_categoria** - Atribuir categoria ao contato
6. **busca_duckduckgo** - Busca complementar de informações

## 📊 Monitoramento

- Logs disponíveis no EasyPanel
- Métricas de uso via console
- Debug ativado para troubleshooting

## 🔄 Deploy Automático

1. Faça push para a branch `migracao-n8n-agno`
2. EasyPanel detecta mudanças automaticamente
3. Build e deploy são executados
4. Aplicação fica disponível no endpoint configurado

## ✅ Teste de Funcionamento

Após o deploy, teste com:
```bash
curl -X POST https://your-domain.com/v1/playground/agents/Alice/runs \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Olá, onde fica o terminal rodoviário de Sinop?",
    "session_id": "test_123",
    "contact_id": "456",
    "conversation_id": "107",
    "custom_attributes_city": "Sinop",
    "custom_attributes_category": "Passageiro"
  }'
```

## 🚨 Troubleshooting

- **Erro de build**: Verifique `requirements.txt`
- **Erro de start**: Confirme variáveis de ambiente
- **Timeout**: Aumente timeout no EasyPanel
- **API errors**: Valide tokens das APIs
