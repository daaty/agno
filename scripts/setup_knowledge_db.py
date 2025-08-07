import psycopg2
from psycopg2 import sql

CONN_STR = "postgres://n8n_user:n8n_pw@148.230.73.27:5432/n8n_db?sslmode=disable"

CREATE_EXTENSION = "CREATE EXTENSION IF NOT EXISTS vector;"

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    embedding VECTOR(1536),
    metadata JSONB
);
"""

def main():
    print("Conectando ao PostgreSQL...")
    conn = psycopg2.connect(CONN_STR)
    conn.autocommit = True
    cur = conn.cursor()
    print("Criando extensão pgvector (se necessário)...")
    cur.execute(CREATE_EXTENSION)
    print("Criando tabela knowledge_documents (se necessário)...")
    cur.execute(CREATE_TABLE)
    print("Setup concluído com sucesso!")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
