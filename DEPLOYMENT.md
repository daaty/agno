# 🚀 INSTRUÇÕES DE DEPLOYMENT - URBAN ALICE AGENT

## Problema Identificado
Na VPS, a base de conhecimento está vazia porque o script de importação não foi executado.

## Solução Implementada
✅ **Inicialização automática** na inicialização do `playground.py`
✅ **Script de deployment** para forçar criação da base
✅ **Scripts específicos para Heroku/EasyPanel**
✅ **Endpoints de debug** para verificar status

---

## 🔧 DEPLOY NO HEROKU/EASYPANEL

### Configuração Automática
✅ **Procfile configurado:**
```
web: python heroku_init.py && uvicorn playground:app --host 0.0.0.0 --port $PORT
```

### Arquivos Necessários
Certifique-se de que estes arquivos estão no repositório:
- `playground.py` (aplicação principal com inicialização automática)
- `knowledge_base.md` (base de conhecimento da Urban)
- `heroku_init.py` (script de inicialização para Heroku)
- `Procfile` (configuração de deploy)

### Deploy Automático
O Heroku executará automaticamente:
1. `python heroku_init.py` - Popula a base de conhecimento
2. `uvicorn playground:app` - Inicia a aplicação

### Logs de Deploy
Você verá logs como:
```
[HEROKU-INIT] 🚀 HEROKU/EASYPANEL DEPLOYMENT - INITIALIZING KNOWLEDGE BASE
[HEROKU-INIT] ✅ Found knowledge_base.md
[HEROKU-INIT] ✅ Processed 9 sections
[HEROKU-INIT] ✅ 9 sections inserted successfully
[HEROKU-INIT] 🎉 SUCCESS! Knowledge base has 9 documents
[HEROKU-INIT] ✅ HEROKU DEPLOYMENT READY - KNOWLEDGE BASE POPULATED!
```

---

## 🔧 DEPLOY MANUAL EM VPS

### Passo 1: Upload dos Arquivos
Certifique-se de que estes arquivos estão na VPS:
- `playground.py` (atualizado com inicialização automática)
- `knowledge_base.md` (arquivo com dados da Urban)
- `init_deployment.py` (script de inicialização)

### Passo 2: Executar Script de Inicialização
```bash
cd /seu/diretorio/do/projeto
python init_deployment.py
```

Este script:
- ✅ Verifica se `knowledge_base.md` existe
- ✅ Cria o diretório `tmp/` se necessário
- ✅ Popula a base de conhecimento com 9 seções
- ✅ Confirma que todos os dados foram inseridos

### Passo 3: Iniciar o Playground
```bash
python playground.py
```

O `playground.py` agora tem **inicialização automática** que:
- Verifica se a base de conhecimento existe
- Se estiver vazia, importa automaticamente do `knowledge_base.md`
- Logs claros para debugging

---

## 🔍 VERIFICAÇÃO DE STATUS

### Via Endpoints de Debug

**Verificar status da base:**
```
GET http://sua-vps:porta/debug/knowledge
```

**Recarregar base de conhecimento:**
```
POST http://sua-vps:porta/debug/reload-knowledge
```

### Via Logs
Procure por estas mensagens nos logs:
```
[STARTUP] ✅ Base de conhecimento OK com 9 documentos
[LOG] busca_knowledge_base_tool chamado com query=...
[DEBUG] Total de sessões encontradas: 9
```

---

## 🚨 TROUBLESHOOTING

### Se a base continuar vazia:

1. **Verificar arquivo knowledge_base.md:**
   ```bash
   ls -la knowledge_base.md
   cat knowledge_base.md | head -20
   ```

2. **Executar script de deployment:**
   ```bash
   python init_deployment.py
   ```

3. **Verificar permissões:**
   ```bash
   chmod 755 tmp/
   chmod 644 knowledge_base.md
   ```

4. **Testar endpoint de debug:**
   ```bash
   curl http://localhost:8000/debug/knowledge
   ```

### Se ainda não funcionar:
- Verifique se o arquivo `knowledge_base.md` está no mesmo diretório que `playground.py`
- Confirme se o diretório `tmp/` tem permissão de escrita
- Execute `init_deployment.py` novamente para forçar recriação

---

## 📊 RESULTADO ESPERADO

Após o deployment correto, você deve ver:

**Logs de inicialização:**
```
[STARTUP] ✅ Base de conhecimento OK com 9 documentos
```

**Logs de busca funcionando:**
```
[LOG] busca_knowledge_base_tool chamado com query=propósito da Urban
[DEBUG] Total de sessões encontradas: 9
[DEBUG] MATCH encontrado! Título: 'Propósito da Urban', Razões: ["'propósito' no título", "'urban' no título"]
[LOG] Encontrados 9 resultados na knowledge base
[LOG] Melhor resultado: 'Propósito da Urban' (relevância: 2)
```

**Endpoint de debug retornando:**
```json
{
  "status": "populated",
  "count": 9,
  "titles": ["Propósito da Urban", "Sistema de Créditos", ...]
}
```

---

## 🎯 PRÓXIMOS PASSOS

1. Execute `python init_deployment.py` na VPS
2. Inicie `python playground.py`
3. Teste uma query: "Qual o propósito da Urban?"
4. Verifique os logs para confirmar que a busca está funcionando
5. Use `/debug/knowledge` para monitorar o status

A Alice agora deve responder perguntas sobre a Urban usando a base de conhecimento local! 🎉
