# Plano Técnico de Migração n8n → Agno

## Checklist de Migração

- [x] Instalar dependências Python (Agno, requests, dotenv, etc.)
- [x] Estruturar diretórios: `playground.py`, `tools/`, `scripts/`, `README.md`
- [x] Definir agente principal (Alice) com instruções do n8n
- [x] Configurar modelo (Gemini, OpenAI, LM Studio)
- [x] Configurar memória (SqliteStorage ou Postgres)
- [x] Ativar knowledge base (`knowledge=True`)
- [ ] Migrar ferramentas customizadas do n8n para Python (HTTP, lógica, raciocínio)
- [ ] Implementar fluxo de atendimento (verificação, coleta, transferências)
- [ ] Testar integração com Chatwoot (endpoints, tokens, payloads)
- [ ] Inserir dados na knowledge base (scripts, API, importação)
- [ ] Validar persistência e consulta de dados
- [ ] Testar todos os fluxos no Playground
- [ ] Documentar código, exemplos e instruções

---

## Próximo Passo

**Migrar ferramentas customizadas do n8n para Python:**
- Criar as ferramentas HTTP (atribui_a_cidade, contato_categoria, suporte, cadastros, duvidas) em `tools/`.
- Implementar a lógica de cada ferramenta conforme o fluxo do n8n.
- Usar variáveis de ambiente para tokens e credenciais.

Deseja começar pela ferramenta de suporte (transferência Chatwoot) ou por outra? Posso gerar o template Python para qualquer uma delas.

---

## Referências ao Fluxo n8n (JS)

- Ferramentas n8n são nodes JS, geralmente baseados em HTTP requests, lógica condicional e manipulação de JSON.
- Para migrar para Python/Agno:
    - Use a biblioteca `requests` para replicar chamadas HTTP (PATCH/POST/GET)
    - Use classes customizadas para cada ferramenta (exemplo abaixo)
    - Adapte lógica condicional do JS para Python (if/else, try/except)
    - Use métodos do Agno para persistência e consulta de dados

### Exemplo: Ferramenta HTTP (Python)
```python
import requests
class SuporteTool:
    def __init__(self, token):
        self.token = token
    def transferir(self, conversation_id):
        url = f"https://chat.urbanmt.com.br/api/v1/accounts/1/conversations/{conversation_id}/assignments"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}
        body = {"team_id": 1}
        response = requests.post(url, json=body, headers=headers)
        return response.json()
```

### Exemplo: Inserção de Knowledge Base
```python
from agno.storage.sqlite import SqliteStorage
storage = SqliteStorage(table_name="knowledge", db_file="tmp/agents.db")
storage.insert({"title": "Como cadastrar cidade", "content": "Para cadastrar a cidade, use a ferramenta atribui_a_cidade..."})
```

---

## Boas Práticas

- Separe cada ferramenta em um arquivo Python dentro de `tools/`
- Use variáveis de ambiente para tokens e credenciais (arquivo `.env`)
- Valide todos os dados antes de enviar para APIs externas
- Documente cada função e classe com docstrings
- Teste cada ferramenta isoladamente antes de integrar ao agente
- Use logs para depuração e monitoramento
- Mantenha o fluxo de atendimento claro e modular
- Atualize o README com exemplos de uso e instruções de configuração

---

## Dicas para Migração

- Analise cada node do n8n (JS) e crie um equivalente Python
- Ferramentas HTTP: requests + tratamento de erros
- Ferramentas de raciocínio: ReasoningTools ou customizadas
- Knowledge base: scripts para importar dados, consultas via agente
- Fluxo: Implemente etapas como funções/métodos, use decorators para validação
- Teste com dados reais e simulações de conversas

---

## Referências Úteis
- [Agno Docs](https://github.com/daaty/agno)
- [requests](https://docs.python-requests.org/en/latest/)
- [dotenv](https://pypi.org/project/python-dotenv/)
- [n8n Docs](https://docs.n8n.io/)
- [Chatwoot API](https://www.chatwoot.com/developers/api)

---

**Sugestão:**
- Crie um script de importação para migrar dados do n8n (JSON) para a knowledge base do Agno
- Use testes automatizados para validar cada etapa
- Mantenha o projeto versionado no Git
