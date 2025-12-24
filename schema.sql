CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    chunk_text TEXT NOT NULL,
    embedding vector(768),
    filename VARCHAR(255) NOT NULL,
    split_strategy VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_filename ON document_chunks(filename);
   
CREATE INDEX IF NOT EXISTS idx_split_strategy ON document_chunks(split_strategy);
