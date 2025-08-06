#!/usr/bin/env python3
"""
Script de inicialização para deployment - força criação da base de conhecimento
Execute antes do playground.py em produção para garantir que a base esteja populada
"""

import os
import sys
from pathlib import Path

# Garante que estamos no diretório correto
script_dir = Path(__file__).parent
os.chdir(script_dir)

# Adiciona o path para encontrar os módulos do agno
sys.path.insert(0, str(script_dir))

def force_knowledge_base_creation():
    """
    Força a criação da base de conhecimento, mesmo que já exista.
    Útil para garantir que a versão mais recente dos dados esteja carregada.
    """
    print("=" * 60)
    print("🚀 INICIALIZADOR DE DEPLOYMENT - URBAN KNOWLEDGE BASE")
    print("=" * 60)

    try:
        from agno.storage.sqlite import SqliteStorage
        from agno.storage.session.agent import AgentSession

        # Configuração
        agent_storage = "tmp/agents.db"
        knowledge_file = "knowledge_base.md"

        # Cria o diretório tmp se não existir
        os.makedirs("tmp", exist_ok=True)

        print(f"📂 Diretório de trabalho: {os.getcwd()}")
        print(f"💾 Arquivo de banco: {agent_storage}")
        print(f"📖 Arquivo de conhecimento: {knowledge_file}")

        # Verifica se o arquivo knowledge_base.md existe
        if not os.path.exists(knowledge_file):
            print(f"❌ ERRO: {knowledge_file} não encontrado!")
            print(f"   Arquivo deve estar em: {os.path.abspath(knowledge_file)}")
            return False

        print(f"✅ Arquivo {knowledge_file} encontrado")

        # Conecta ao storage
        storage = SqliteStorage(table_name="knowledge", db_file=agent_storage)
        print(f"✅ Conexão com SQLite estabelecida")

        # Verifica estado atual
        existing_sessions = storage.get_all_sessions()
        if existing_sessions:
            print(f"⚠️  Base atual tem {len(existing_sessions)} documentos - será atualizada")
        else:
            print(f"📋 Base vazia - será populada")

        # Lê o arquivo knowledge_base.md
        print(f"📖 Lendo {knowledge_file}...")
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"✅ Arquivo lido ({len(content)} caracteres)")

        # Processa as seções
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

        print(f"✅ Processadas {len(sections)} seções")

        # Lista as seções encontradas
        for i, section in enumerate(sections, 1):
            print(f"   {i}. {section['title']}")

        # Insere no banco
        print(f"💾 Inserindo seções no banco...")
        inserted_count = 0

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
                inserted_count += 1

        print(f"✅ {inserted_count} seções inseridas com sucesso")

        # Verifica resultado final
        final_sessions = storage.get_all_sessions()
        if final_sessions and len(final_sessions) > 0:
            print(f"🎉 SUCESSO! Base de conhecimento tem {len(final_sessions)} documentos")
            print("\n📋 Documentos na base:")
            for session in final_sessions:
                if hasattr(session, 'session_data') and session.session_data:
                    title = session.session_data.get("title", "Sem título")
                    content_size = len(session.session_data.get("content", ""))
                    print(f"   ✓ {title} ({content_size} chars)")

            print("\n" + "=" * 60)
            print("✅ DEPLOYMENT READY - KNOWLEDGE BASE POPULATED!")
            print("=" * 60)
            return True
        else:
            print("❌ ERRO: Base de conhecimento vazia após importação")
            return False

    except Exception as e:
        print(f"❌ ERRO durante inicialização: {e}")
        import traceback
        print("📋 Traceback completo:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = force_knowledge_base_creation()
    sys.exit(0 if success else 1)
