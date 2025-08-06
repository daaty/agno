# Plano de Migração do Agente n8n para Agno

## 1. Preparação do Ambiente

- Instale o Agno e dependências (requests, etc.)
- Crie diretório para o projeto e banco de dados (ex: `tmp/agents.db`)

## 2. Definição do Agente Principal

- Crie um agente chamado "Alice" com instruções detalhadas do n8n
- Configure o modelo (Gemini, OpenAI, LM Studio)
- Configure memória (SqliteStorage ou Postgres)
- Ative o parâmetro `knowledge=True` para habilitar a base de conhecimento (RAG)

## 3. Implementação das Ferramentas

- **Think:** Use ReasoningTools ou crie uma ferramenta customizada para raciocínio intermediário
- **knowledg_base:** Utilize o parâmetro `knowledge=True` e insira dados/documentos no storage do agente para consulta tipo RAG
    - Insira dados via script, API ou ferramenta customizada
    - O agente poderá consultar esses dados durante a conversa
- **atribui_a_cidade:** Crie uma ferramenta customizada que faz PATCH na API do Chatwoot
- **contato_categoria:** Crie uma ferramenta customizada que faz PATCH na API do Chatwoot
- **suporte, cadastros, duvidas:** Crie ferramentas customizadas que fazem POST na API do Chatwoot com o team_id correto

## 4. Configuração do Fluxo de Atendimento

- Implemente lógica de verificação/coleta de cidade e categoria
- Implemente análise de intenção e regras de transferência
- Garanta que o agente sempre use Think antes de executar ferramentas
- Implemente respostas com tom humanizado conforme instruções
- Garanta que o agente consulte a base de conhecimento (RAG) quando necessário

## 5. Integração com Chatwoot

- Configure autenticação (token) nas ferramentas HTTP
- Teste endpoints e payloads para cada ação

## 6. Persistência de Memória e Knowledge Base

- Configure SqliteStorage ou integração com Postgres para histórico de conversas
- Insira documentos/dados relevantes no storage para consulta pelo agente

## 7. Testes e Validação

- Teste o agente no Playground do Agno
- Valide todos os fluxos: coleta de dados, transferências, atualizações de atributos, consultas à base de conhecimento
- Ajuste instruções e ferramentas conforme necessário

## 8. Documentação e Manutenção

- Documente o código e instruções de uso
- Crie README com exemplos de uso e instruções de configuração
- Documente como inserir e consultar dados na base de conhecimento

---

**Sugestão de Estrutura de Arquivos:**

- `playground.py` (agente principal e playground)
- `tools/` (ferramentas customizadas)
- `scripts/` (inserção de dados na knowledge base)
- `README.md` (documentação)

**Próximos Passos:**

1. Gerar exemplos de código para cada ferramenta customizada
2. Montar o agente principal com todas as instruções e knowledge base
3. Testar integração, inserção/consulta de dados e ajustar conforme feedback
