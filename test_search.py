#!/usr/bin/env python3

# Teste da nova função de busca melhorada
import os
import sys
sys.path.append('.')

from agno.storage.sqlite import SqliteStorage

def busca_knowledge_base_test(query: str):
    """Teste da função de busca melhorada"""
    print(f"[TEST] Testando busca com query: {query}")

    try:
        # Conecta na mesma tabela que o script de importação usa
        storage = SqliteStorage(table_name="knowledge", db_file="tmp/agents.db")

        # Busca por palavras-chave no título ou conteúdo (case-insensitive)
        query_lower = query.lower()
        print(f"[DEBUG] Query convertida para lowercase: {query_lower}")

        # Cria uma lista de palavras-chave da query para busca mais flexível
        keywords = [word.strip() for word in query_lower.split() if len(word.strip()) > 2]
        print(f"[DEBUG] Palavras-chave extraídas: {keywords}")

        # Usa o método get_all_sessions do SqliteStorage
        all_sessions = storage.get_all_sessions()
        print(f"[DEBUG] Total de sessões encontradas: {len(all_sessions) if all_sessions else 0}")

        # Filtra resultados que contenham qualquer palavra-chave no título ou conteúdo
        matches = []
        for session in all_sessions:
            if hasattr(session, 'session_data') and session.session_data:
                session_data = session.session_data
                title = session_data.get("title", "").lower()
                content = session_data.get("content", "").lower()

                # Busca flexível: se qualquer palavra-chave estiver no título ou conteúdo
                match_found = False
                match_reasons = []

                for keyword in keywords:
                    if keyword in title:
                        match_found = True
                        match_reasons.append(f"'{keyword}' no título")
                    elif keyword in content:
                        match_found = True
                        match_reasons.append(f"'{keyword}' no conteúdo")

                if match_found:
                    print(f"[DEBUG] MATCH encontrado! Título: '{session_data.get('title', '')}', Razões: {match_reasons}")
                    # Calcula relevância baseada no número de matches
                    relevance = len(match_reasons)
                    matches.append({
                        "title": session_data.get("title", ""),
                        "content": session_data.get("content", "")[:200] + "...",  # Preview
                        "relevance": relevance,
                        "match_reasons": match_reasons
                    })

        # Ordena por relevância (mais matches primeiro)
        matches.sort(key=lambda x: x["relevance"], reverse=True)
        print(f"[DEBUG] Total de matches encontrados: {len(matches)}")

        if matches:
            print(f"[SUCCESS] Encontrados {len(matches)} resultados!")
            for i, match in enumerate(matches[:2]):  # Top 2 resultados
                print(f"  {i+1}. '{match['title']}' (relevância: {match['relevance']})")
                print(f"     Razões: {match['match_reasons']}")
                print(f"     Preview: {match['content']}")
                print()
            return True
        else:
            print(f"[FAIL] Nenhum resultado encontrado para: {query}")
            return False

    except Exception as e:
        print(f"[ERRO] Erro ao buscar na knowledge base: {e}")
        import traceback
        print(f"[ERRO] Traceback completo: {traceback.format_exc()}")
        return False

# Testes com as queries que estavam falhando
test_queries = [
    "cadastro motorista Urban",
    "propósito da Urban",
    "cadastro de motorista",
    "como tornar-se motorista",
    "Urban créditos"
]

print("=== TESTE DA BUSCA NA KNOWLEDGE BASE ===\n")
for query in test_queries:
    busca_knowledge_base_test(query)
    print("-" * 60)
    print()
