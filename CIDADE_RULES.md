# 🏙️ REGRAS CRÍTICAS DE ATRIBUIÇÃO DE CIDADE

## ⚠️ REGRA FUNDAMENTAL

A **atribuição de cidade** é um **custom attribute** cadastrado como **lista fixa** no Chatwoot. Os nomes das cidades devem ser enviados **EXATAMENTE** como cadastrados na API, caso contrário a atribuição **FALHARÁ**.

---

## 📋 LISTA OFICIAL DE CIDADES (API Chatwoot)

```
✅ NOMES EXATOS aceitos pela API:
- Matupa           (sem acento)
- Guaranta         (sem acento)
- Peixoto          (nome curto)
- Monte Verde      (duas palavras)
- Bandeirantes     (completo)
- Alta Floresta    (duas palavras)
- Nova Canaa       (sem acento)
- Colider          (sem acento)
```

---

## 🔄 NORMALIZAÇÃO AUTOMÁTICA

O agente **automaticamente normaliza** variações comuns:

### ✅ Variações Aceitas → Nome Oficial:
- `"Matupá"` → `"Matupa"`
- `"matupa"` → `"Matupa"`
- `"MATUPA"` → `"Matupa"`
- `"Guarantã"` → `"Guaranta"`
- `"Guarantã do Norte"` → `"Guaranta"`
- `"Peixoto de Azevedo"` → `"Peixoto"`
- `"alta floresta"` → `"Alta Floresta"`
- `"Nova Canaã"` → `"Nova Canaa"`
- `"Nova Canaã do Norte"` → `"Nova Canaa"`
- `"Nova Monte Verde"` → `"Monte Verde"`
- `"Colidér"` → `"Colider"`

### ❌ Cidades NÃO suportadas:
- `"Cuiabá"` → **ERRO**
- `"São Paulo"` → **ERRO**
- `"Outras cidades"` → **ERRO**

---

## 🔧 IMPLEMENTAÇÃO TÉCNICA

### 1. **Lógica no playground.py:**
```python
def atribui_cidade_tool(contact_id: str, cidade: str):
    # Normalização automática de variações
    cidades_validas = {
        "matupa": "Matupa",
        "matupá": "Matupa",
        "guaranta": "Guaranta",
        # ... outras variações
    }

    cidade_normalizada = cidade.lower().strip()

    if cidade_normalizada in cidades_validas:
        cidade_final = cidades_validas[cidade_normalizada]
        # Envia para AtribuiCidadeTool
    else:
        # Retorna erro com lista de cidades válidas
```

### 2. **Formato JSON (AtribuiCidadeTool):**
```json
{
  "custom_attributes": {
    "cidade": "Matupa"
  }
}
```

### 3. **Instruções do Agente:**
```
"ATRIBUIÇÃO DE CIDADE - REGRA CRÍTICA: Use APENAS os nomes EXATOS desta lista:
Matupa, Guaranta, Peixoto, Monte Verde, Bandeirantes, Alta Floresta, Nova Canaa, Colider.
Normalize variações automaticamente para os nomes exatos."
```

---

## 🎯 COMPORTAMENTO ESPERADO

### ✅ **Cenário 1: Cidade válida com variação**
**Usuário:** "Sou de Matupá"
**Alice:** Normaliza `Matupá` → `Matupa` e atribui com sucesso

### ✅ **Cenário 2: Cidade já no contexto**
**Contexto:** `custom_attributes_city: "Colider"`
**Alice:** NÃO pergunta cidade, usa informação existente

### ❌ **Cenário 3: Cidade inválida**
**Usuário:** "Sou de Cuiabá"
**Alice:** "Cidade inválida. Cidades aceitas: Matupa, Guaranta, Peixoto..."

### ✅ **Cenário 4: Atribuição bem-sucedida**
**Log:** `[LOG] Cidade normalizada de 'peixoto de azevedo' para 'Peixoto'`
**API:** Recebe `{"custom_attributes": {"cidade": "Peixoto"}}`

---

## 🚨 PONTOS CRÍTICOS

1. **NUNCA** pergunte cidade se `custom_attributes_city` existir no contexto
2. **SEMPRE** normalize variações para nomes oficiais da API
3. **JAMAIS** use nomes fora da lista oficial
4. **SEMPRE** use o formato JSON com `custom_attributes`
5. **SEMPRE** use o `contact_id` EXATO do contexto

---

## 📊 VERIFICAÇÃO

### Teste de Funcionamento:
1. **Usuário diz:** "Sou de Matupá"
2. **Esperado:** Alice normaliza para "Matupa" e atribui
3. **Log:** `[LOG] Cidade normalizada de 'Matupá' para 'Matupa'`
4. **API:** Recebe exatamente `{"custom_attributes": {"cidade": "Matupa"}}`

### Validação de Erro:
1. **Usuário diz:** "Sou de São Paulo"
2. **Esperado:** Alice retorna erro com lista de cidades válidas
3. **Log:** `[ERRO] Cidade inválida: 'São Paulo'`

**Esta regra é FUNDAMENTAL para o funcionamento correto da atribuição de cidade!** ⚠️
