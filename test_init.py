#!/usr/bin/env python3

# Teste da função de inicialização automática
import os
import sys
sys.path.append('.')

from agno.storage.sqlite import SqliteStorage

# Testa a função ensure_knowledge_base_startup
def test_ensure_knowledge():
    """Testa a função de garantia da base de conhecimento"""
    print("=== TESTE DA INICIALIZAÇÃO AUTOMÁTICA ===")

    # Simula a função do playground.py
    agent_storage = "tmp/agents_test.db"

    def ensure_knowledge_base_startup():
        """
        Garante que a base de conhecimento esteja populada na inicialização.
        """
        print(f"[STARTUP] Verificando base de conhecimento...")

        try:
            # Verifica se já existe dados na base
            storage = SqliteStorage(table_name="knowledge", db_file=agent_storage)
            existing_sessions = storage.get_all_sessions()

            if existing_sessions and len(existing_sessions) > 0:
                print(f"[STARTUP] ✅ Base de conhecimento OK com {len(existing_sessions)} documentos")
                return True

            print(f"[STARTUP] ⚠️  Base de conhecimento vazia. Importando dados...")

            # Importa dados do knowledge_base.md
            knowledge_file = "knowledge_base.md"
            if not os.path.exists(knowledge_file):
                print(f"[STARTUP] ❌ Arquivo knowledge_base.md não encontrado")
                return False

            # Lê e processa o arquivo markdown
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Divide por seções usando o padrão # Título
            from agno.storage.session.agent import AgentSession

            sections = []
            current_section = {"title": "", "content": ""}

            for line in content.split('\n'):
                if line.startswith('# ') and not line.startswith('##'):
                    # Nova seção encontrada
                    if current_section["title"]:  # Salva seção anterior se existir
                        sections.append(current_section)
                    current_section = {
                        "title": line[2:].strip(),  # Remove '# '
                        "content": ""
                    }
                else:
                    # Adiciona linha ao conteúdo da seção atual
                    current_section["content"] += line + '\n'

            # Adiciona a última seção
            if current_section["title"]:
                sections.append(current_section)

            # Insere seções no banco usando AgentSession
            for i, section in enumerate(sections):
                if section["title"] and section["content"].strip():
                    session = AgentSession(
                        session_id=f"kb_{i+1}",
                        agent_id="knowledge_base",
                        user_id="system"
                    )

                    # Armazena os dados da seção no session_data
                    session.session_data = {
                        "title": section["title"],
                        "content": section["content"].strip()
                    }

                    storage.upsert(session)

            # Verifica se a importação funcionou
            final_sessions = storage.get_all_sessions()
            print(f"[STARTUP] ✅ Base de conhecimento importada! {len(final_sessions)} documentos inseridos.")

            return True

        except Exception as e:
            print(f"[STARTUP] ❌ Erro ao garantir base de conhecimento: {e}")
            import traceback
            print(f"[STARTUP] Traceback: {traceback.format_exc()}")
            return False

    # Executa o teste
    result = ensure_knowledge_base_startup()

    if result:
        print("\n✅ TESTE PASSOU! Função de inicialização funciona.")

        # Verifica novamente para testar o cenário de "já populado"
        print("\n--- Teste de Segunda Execução ---")
        ensure_knowledge_base_startup()

    else:
        print("\n❌ TESTE FALHOU! Função de inicialização com erro.")

if __name__ == "__main__":
    test_ensure_knowledge()
