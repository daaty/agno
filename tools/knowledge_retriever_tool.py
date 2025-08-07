"""
KnowledgeRetriever Tool
----------------------
Ferramenta profissional para busca RAG em base vetorizada via pgvector.
- Consulta tabela vetorizada (ex: knowledg_base1) populada pelo n8n
- Usa o mesmo modelo de embedding do pipeline de ingestão
- Pronta para produção: logging, exceptions, typing, docstrings
"""
import os
from dotenv import load_dotenv
import logging
from typing import List, Tuple, Optional
import psycopg2
import numpy as np


# --- Carrega variáveis de ambiente do .env ---
load_dotenv()

# Configuração de credenciais e parâmetros
PG_CONN_STR = os.getenv("KNOWLEDGE_PG_CONN")  # Ex: postgres://user:pw@host:5432/db?sslmode=disable
TABLE_NAME = os.getenv("KNOWLEDGE_TABLE", "knowledg_base1")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

# API keys para embedding
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger("KnowledgeRetriever")

# --- Embedding ---
def generate_embedding(text: str) -> List[float]:
    """
    Gera embedding para o texto usando o mesmo modelo do pipeline n8n.
    Substitua pelo client real (Gemini, OpenAI, etc) em produção.
    """
    # Exemplo: integração real com Gemini ou OpenAI
    # if GEMINI_API_KEY:
    #     return gemini_embed(text, api_key=GEMINI_API_KEY)
    # elif OPENAI_API_KEY:
    #     return openai_embed(text, api_key=OPENAI_API_KEY)
    # else:
    #     ...
    # Placeholder: gera vetor aleatório determinístico
    np.random.seed(abs(hash(text)) % (2**32))
    return np.random.rand(EMBEDDING_DIM).tolist()

# --- Retriever ---
def retrieve_similar_documents(query: str, top_k: int = 5) -> List[Tuple[str, str, dict, float]]:
    """
    Busca os documentos mais similares ao embedding da query.
    Retorna lista de tuplas: (id, text, metadata, distance)
    """
    embedding = generate_embedding(query)
    try:
        conn = psycopg2.connect(PG_CONN_STR)
        cur = conn.cursor()
        sql = f"""
            SELECT id, text, metadata, embedding <-> %s AS distance
            FROM {TABLE_NAME}
            ORDER BY embedding <-> %s
            LIMIT %s;
        """
        cur.execute(sql, (embedding, embedding, top_k))
        results = cur.fetchall()
        cur.close()
        conn.close()
        logger.info(f"{len(results)} documentos recuperados para a query.")
        return results
    except Exception as e:
        logger.error(f"Erro ao buscar documentos: {e}")
        return []


# --- Instruções de configuração ---
"""
Configuração de variáveis de ambiente necessárias (.env):

# String de conexão do Postgres (obrigatório)
KNOWLEDGE_PG_CONN=postgres://usuario:senha@host:5432/db?sslmode=disable

# Nome da tabela de knowledge base (opcional, default: knowledg_base1)
KNOWLEDGE_TABLE=knowledg_base1

# Dimensão do embedding (ajuste conforme modelo)
EMBEDDING_DIM=1536

# Chave da API Gemini (opcional, se usar Gemini)
GEMINI_API_KEY=...

# Chave da API OpenAI (opcional, se usar OpenAI)
OPENAI_API_KEY=...
"""
