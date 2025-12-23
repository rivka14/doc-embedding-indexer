-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create document_chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    chunk_text TEXT NOT NULL,
    embedding vector(768),
    filename VARCHAR(255) NOT NULL,
    split_strategy VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on filename for faster queries
CREATE INDEX IF NOT EXISTS idx_filename ON document_chunks(filename);

-- Create index on split_strategy for filtering
CREATE INDEX IF NOT EXISTS idx_split_strategy ON document_chunks(split_strategy);
