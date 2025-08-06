#!/usr/bin/env python3
"""
Script para garantir que a base de conhecimento esteja sempre populada.
Executa automaticamente na inicialização do playground.py
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from agno.storage.sqlite import SqliteStorage
from agno.storage.session.agent import AgentSession

def ensure_knowledge_base(db_file="tmp/agents.db"):
    """
    Garante que a base de conhecimento esteja populada.
    Se estiver vazia, importa automaticamente do knowledge_base.md
    """
    print(f"[INIT] Verificando base de conhecimento...")

    try:
        # Verifica se já existe dados na base
        storage = SqliteStorage(table_name="knowledge", db_file=db_file)
        existing_sessions = storage.get_all_sessions()

        if existing_sessions and len(existing_sessions) > 0:
            print(f"[INIT] ✅ Base de conhecimento já populada com {len(existing_sessions)} documentos")
            return True

        print(f"[INIT] ⚠️  Base de conhecimento vazia. Importando dados...")

        # Importa dados do knowledge_base.md
        knowledge_file = root_dir / "knowledge_base.md"
        if not knowledge_file.exists():
            print(f"[INIT] ❌ Arquivo knowledge_base.md não encontrado em: {knowledge_file}")
            return False

        # Lê e processa o arquivo markdown
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Divide por seções usando o padrão # Título
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
        print(f"[INIT] ✅ Base de conhecimento importada com sucesso! {len(final_sessions)} documentos inseridos.")

        # Lista os títulos importados
        for session in final_sessions:
            if hasattr(session, 'session_data') and session.session_data:
                title = session.session_data.get("title", "Sem título")
                print(f"[INIT]   - {title}")

        return True

    except Exception as e:
        print(f"[INIT] ❌ Erro ao garantir base de conhecimento: {e}")
        import traceback
        print(f"[INIT] Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    ensure_knowledge_base()
