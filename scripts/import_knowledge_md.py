

import os
from agno.storage.sqlite import SqliteStorage
from agno.storage.session.agent import AgentSession

# Configurações
DB_FILE = os.getenv("KNOWLEDGE_DB_FILE", "tmp/agents.db")
TABLE_NAME = os.getenv("KNOWLEDGE_TABLE", "knowledge")
MD_FILE = os.getenv("KNOWLEDGE_MD_FILE", "knowledge_base.md")
AGENT_ID = os.getenv("KNOWLEDGE_AGENT_ID", "alice")

def parse_markdown_sections(md_path):
    docs = []
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()
    current_title = None
    current_content = []
    for line in lines:
        if line.startswith("#"):
            if current_title and current_content:
                docs.append({"title": current_title, "content": "".join(current_content).strip()})
            current_title = line.strip().lstrip("# ")
            current_content = []
        else:
            current_content.append(line)
    if current_title and current_content:
        docs.append({"title": current_title, "content": "".join(current_content).strip()})
    return docs

if __name__ == "__main__":
    storage = SqliteStorage(table_name=TABLE_NAME, db_file=DB_FILE)
    docs = parse_markdown_sections(MD_FILE)
    count = 0
    for i, doc in enumerate(docs):
        session = AgentSession(
            session_id=f"knowledge_{i+1}",
            agent_id=AGENT_ID,
            session_data={"title": doc["title"], "content": doc["content"]}
        )
        try:
            storage.upsert(session)
            count += 1
        except Exception as e:
            print(f"WARNING  Exception upserting into table: {e}")
            print("WARNING  A table upgrade might be required, please    ")
            print("         review these docs for more information:      ")
            print("         https://agno.link/upgrade-schema")
    print(f"{count} documentos inseridos na knowledge base.")
