#!/usr/bin/env python3
"""
Script de inicialização específico para Heroku/EasyPanel
Executa antes do playground.py para garantir que a base de conhecimento esteja populada
"""

import os
import sys
import logging
from pathlib import Path

# Configuração de logging para Heroku
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [HEROKU-INIT] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def heroku_init_knowledge_base():
    """
    Inicialização da base de conhecimento específica para Heroku/EasyPanel
    """
    logger.info("=" * 60)
    logger.info("🚀 HEROKU/EASYPANEL DEPLOYMENT - INITIALIZING KNOWLEDGE BASE")
    logger.info("=" * 60)

    try:
        # Importações dentro da função para evitar problemas de importação
        from agno.storage.sqlite import SqliteStorage
        from agno.storage.session.agent import AgentSession

        # Configuração para ambiente de produção
        agent_storage = "tmp/agents.db"
        knowledge_file = "knowledge_base.md"

        # Cria o diretório tmp se não existir
        os.makedirs("tmp", exist_ok=True)
        logger.info(f"📂 Working directory: {os.getcwd()}")
        logger.info(f"💾 Database file: {agent_storage}")
        logger.info(f"📖 Knowledge file: {knowledge_file}")

        # Verifica se o arquivo knowledge_base.md existe
        if not os.path.exists(knowledge_file):
            logger.error(f"❌ ERROR: {knowledge_file} not found!")
            logger.error(f"   Expected at: {os.path.abspath(knowledge_file)}")
            logger.info("📁 Files in current directory:")
            for file in os.listdir("."):
                logger.info(f"   - {file}")
            return False

        logger.info(f"✅ Found {knowledge_file}")

        # Conecta ao storage
        storage = SqliteStorage(table_name="knowledge", db_file=agent_storage)
        logger.info(f"✅ SQLite connection established")

        # Verifica estado atual (em produção, sempre recriar para garantir versão atual)
        existing_sessions = storage.get_all_sessions()
        if existing_sessions:
            logger.info(f"⚠️  Existing knowledge base has {len(existing_sessions)} documents - will update")
        else:
            logger.info(f"📋 Empty knowledge base - will populate")

        # Lê o arquivo knowledge_base.md
        logger.info(f"📖 Reading {knowledge_file}...")
        try:
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Fallback para diferentes encodings
            with open(knowledge_file, 'r', encoding='latin-1') as f:
                content = f.read()

        logger.info(f"✅ File read successfully ({len(content)} characters)")

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

        logger.info(f"✅ Processed {len(sections)} sections")

        # Lista as seções encontradas (apenas títulos para não poluir logs)
        section_titles = [section['title'] for section in sections]
        logger.info(f"📋 Sections: {', '.join(section_titles)}")

        # Insere no banco
        logger.info(f"💾 Inserting sections into database...")
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

        logger.info(f"✅ {inserted_count} sections inserted successfully")

        # Verifica resultado final
        final_sessions = storage.get_all_sessions()
        if final_sessions and len(final_sessions) > 0:
            logger.info(f"🎉 SUCCESS! Knowledge base has {len(final_sessions)} documents")

            # Conta documentos únicos por título (para caso haja duplicatas)
            unique_titles = set()
            for session in final_sessions:
                if hasattr(session, 'session_data') and session.session_data:
                    title = session.session_data.get("title", "")
                    if title:
                        unique_titles.add(title)

            logger.info(f"📊 Unique documents: {len(unique_titles)}")
            logger.info("=" * 60)
            logger.info("✅ HEROKU DEPLOYMENT READY - KNOWLEDGE BASE POPULATED!")
            logger.info("=" * 60)
            return True
        else:
            logger.error("❌ ERROR: Knowledge base empty after import")
            return False

    except ImportError as e:
        logger.error(f"❌ Import error - missing dependencies: {e}")
        logger.error("Make sure all required packages are installed")
        return False
    except Exception as e:
        logger.error(f"❌ ERROR during initialization: {e}")
        import traceback
        logger.error("📋 Full traceback:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                logger.error(line)
        return False

def main():
    """Main function for Heroku execution"""
    try:
        success = heroku_init_knowledge_base()
        if success:
            logger.info("🚀 Knowledge base initialization completed successfully")
            logger.info("Starting main application...")
            sys.exit(0)
        else:
            logger.error("❌ Knowledge base initialization failed")
            logger.error("Application startup will continue but knowledge base may be empty")
            # Não falha o deploy - continua mesmo se a base não carregar
            sys.exit(0)  # Changed from 1 to 0 to not fail deployment
    except KeyboardInterrupt:
        logger.info("Initialization interrupted")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(0)  # Continue deployment even on unexpected errors

if __name__ == "__main__":
    main()
