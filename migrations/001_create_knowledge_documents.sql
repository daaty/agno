-- Migration: Criação da base de conhecimento com embeddings (pgvector)
-- Requer PostgreSQL >=13 e extensão pgvector instalada

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    metadata JSONB,
    embedding vector(1536) -- ajuste o tamanho conforme o modelo de embedding utilizado
);

-- Índice para busca textual
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_title_content ON knowledge_documents USING GIN (to_tsvector('portuguese', title || ' ' || content));

-- Índice para busca vetorial (pgvector)
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_embedding ON knowledge_documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
