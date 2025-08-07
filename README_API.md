# Documentação Técnica e Operacional da API

## Sumário
- [Visão Geral](#visão-geral)
- [Endpoints Principais](#endpoints-principais)
- [Endpoints de Debug](#endpoints-de-debug)
- [Variáveis de Contexto](#variáveis-de-contexto)
- [Extração Automática de Cidade e Categoria](#extração-automática-de-cidade-e-categoria)
- [Checklist de Produção](#checklist-de-produção)
- [Troubleshooting](#troubleshooting)
- [Instruções para Desenvolvedores](#instruções-para-desenvolvedores)

---

## Visão Geral
Esta API FastAPI centraliza o atendimento inteligente da Urban, com extração automática de cidade e categoria, fallback robusto, logging detalhado, memória otimizada e integração com Chatwoot.

- **Arquivo principal:** `playground.py`
- **Configuração de cidades:** `config/cidades.json`
- **Base de conhecimento:** `knowledge_base.md` (importada para SQLite)
- **Testes automatizados:** `tests/`

---

## Endpoints Principais

### `POST /v1/playground/agents/{agent_id}/runs`
Executa o agente Alice com contexto e mensagem do usuário.

**Payload:**
```
{
  "message": "<mensagem do usuário>",
  "session_id": "<id da sessão>",
  "user_id": "<opcional>",
  "contact_id": "<opcional>",
  "conversation_id": "<opcional>",
  "custom_attributes_city": "<opcional>",
  "custom_attributes_category": "<opcional>"
}
```
**Resposta:** JSON com resultado, tempo de processamento e timestamp.

### `GET /health`
Health check detalhado do sistema, status da base de conhecimento, caches e versão.

---

## Endpoints de Debug

- `GET /debug/knowledge` — Status e estatísticas da base de conhecimento.
- `POST /debug/reload-knowledge` — Força recarregamento/importação da base de conhecimento.
- `GET /debug/memory/{session_id}` — Mostra memória factual e de contexto do agente para a sessão.
- `GET /debug/cache` — Status dos caches.
- `POST /debug/cache/clear` — Limpa todos os caches.

---

## Variáveis de Contexto
As variáveis de contexto são extraídas do payload e usadas para garantir respostas corretas e uso seguro das ferramentas:

- `user_id`, `contact_id`, `conversation_id`: IDs explícitos do contexto.
- `custom_attributes_city`, `custom_attributes_category`: Cidade e categoria já informadas.
- `CIDADE_JA_INFORMADA`, `CATEGORIA_JA_INFORMADA`: Flags booleanas para controle de fluxo.
- `CONVERSATION_ID_ATUAL`, `CONTACT_ID_ATUAL`, `CIDADE_ATUAL`, `CATEGORIA_ATUAL`: Sempre use estes valores para ferramentas.

---

## Extração Automática de Cidade e Categoria
- O agente extrai e normaliza cidade e categoria automaticamente da mensagem do usuário usando regex e dicionário de cidades.
- Se não for possível extrair, faz fallback e loga um warning.
- As informações extraídas são salvas em `context_memory` e usadas para evitar perguntas repetidas.
- Toda extração, sucesso ou falha, é registrada no log (`playground.log`).

---

## Checklist de Produção
- [ ] Variáveis de ambiente (.env) configuradas (`OPENAI_API_KEY`, etc)
- [ ] Arquivo `config/cidades.json` presente e válido
- [ ] Base de conhecimento importada (`knowledge_base.md`)
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Testes automatizados passando (`pytest tests/`)
- [ ] Logging ativo e monitorado (`playground.log`)
- [ ] Endpoints de health/debug acessíveis
- [ ] Rate limiting e cache funcionando

---

## Troubleshooting
- **Falha na extração de cidade/categoria:** Verifique logs para mensagens `[MEMORY][FALLBACK]`.
- **Base de conhecimento vazia:** Use `/debug/reload-knowledge` e confira o arquivo `knowledge_base.md`.
- **Erros de validação:** Cheque se os IDs e atributos enviados no payload estão corretos.
- **Problemas de performance:** Monitore o tamanho dos caches e o tempo de resposta nos logs.

---

## Instruções para Desenvolvedores
- Todo o código principal está em `playground.py`.
- Para adicionar cidades, edite `config/cidades.json`.
- Para expandir a base de conhecimento, edite `knowledge_base.md` e recarregue.
- Para rodar localmente:
  ```
  python playground.py
  ```
- Para rodar testes:
  ```
  pytest tests/
  ```
- Para logs detalhados, consulte `playground.log`.

---

Dúvidas ou sugestões? Consulte o código, os testes ou abra uma issue.
