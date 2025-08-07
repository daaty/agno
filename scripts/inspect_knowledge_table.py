import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
PG_CONN_STR = os.getenv("KNOWLEDGE_PG_CONN")
TABLE_NAME = os.getenv("KNOWLEDGE_TABLE", "knowledg_base1")

conn = psycopg2.connect(PG_CONN_STR)
cur = conn.cursor()
cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s", (TABLE_NAME,))
columns = cur.fetchall()
print(f"Colunas da tabela {TABLE_NAME}:")
for col, dtype in columns:
    print(f"- {col} ({dtype})")
cur.close()
conn.close()
