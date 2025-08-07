import os
from dotenv import load_dotenv
import psycopg2
import numpy as np

load_dotenv()
PG_CONN_STR = os.getenv("KNOWLEDGE_PG_CONN")
TABLE_NAME = os.getenv("KNOWLEDGE_TABLE", "knowledg_base1")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

def generate_embedding(text: str):
    np.random.seed(abs(hash(text)) % (2**32))
    return np.random.rand(EMBEDDING_DIM).tolist()

def retrieve_similar_documents(query: str, top_k: int = 5):
    embedding = generate_embedding(query)
    conn = psycopg2.connect(PG_CONN_STR)
    cur = conn.cursor()
    sql = f"""
        SELECT id, text, metadata, embedding <-> (%s::vector) AS distance
        FROM {TABLE_NAME}
        ORDER BY embedding <-> (%s::vector)
        LIMIT %s;
    """
    cur.execute(sql, (embedding, embedding, top_k))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

if __name__ == "__main__":
    query = input("Digite sua pergunta: ")
    docs = retrieve_similar_documents(query)
    for i, (doc_id, text, metadata, distance) in enumerate(docs, 1):
        print(f"\nDocumento #{i} (id={doc_id}, distância={distance:.4f}):\nTrecho: {text[:300]}...\nMetadados: {metadata}")
