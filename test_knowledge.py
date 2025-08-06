#!/usr/bin/env python3

from agno.storage.sqlite import SqliteStorage

# Testa a conexão e leitura da base de conhecimento
try:
    storage = SqliteStorage(table_name="knowledge", db_file="tmp/agents.db")
    print("✅ Conexão com SQLiteStorage estabelecida")

    # Tenta obter todas as sessões
    sessions = storage.get_all_sessions()
    print(f"📊 Total de sessões encontradas: {len(sessions) if sessions else 0}")

    if sessions:
        print("\n📋 Primeiras 3 sessões:")
        for i, session in enumerate(sessions[:3]):
            if hasattr(session, 'session_data') and session.session_data:
                title = session.session_data.get("title", "Sem título")
                content_preview = session.session_data.get("content", "")[:100]
                print(f"  {i+1}. Título: '{title}'")
                print(f"     Conteúdo (100 chars): '{content_preview}...'")
            else:
                print(f"  {i+1}. Sessão sem session_data")

        # Teste de busca específica
        test_queries = ["propósito", "urban", "motorista", "cadastro"]
        for query in test_queries:
            matches = 0
            for session in sessions:
                if hasattr(session, 'session_data') and session.session_data:
                    title = session.session_data.get("title", "").lower()
                    content = session.session_data.get("content", "").lower()
                    if query.lower() in title or query.lower() in content:
                        matches += 1
            print(f"🔍 Query '{query}': {matches} resultados")
    else:
        print("❌ Nenhuma sessão encontrada")

except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    import traceback
    print(traceback.format_exc())
