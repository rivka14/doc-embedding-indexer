# Document Embedding Indexer

A Python tool that extracts text from PDF and DOCX files, splits it into chunks using various strategies, generates embeddings using Google Gemini API, and stores them in PostgreSQL with pgvector for efficient vector similarity search.

## Features

- **Text Extraction**: Supports PDF and DOCX file formats
- **Flexible Chunking**: Three text chunking strategies:
  - Fixed-size with overlap
  - Sentence-based splitting
  - Paragraph-based splitting
- **Embeddings**: Google Gemini API integration for generating high-quality embeddings
- **Vector Storage**: PostgreSQL with pgvector extension for efficient vector search
- **CLI Interface**: Simple command-line interface for easy usage

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Google Gemini API key

## Installation

### 1. Install PostgreSQL

**macOS (using Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download and install from [PostgreSQL official website](https://www.postgresql.org/download/windows/)

### 2. Install pgvector Extension

**macOS (using Homebrew):**
```bash
brew install pgvector
```

**Ubuntu/Debian:**
```bash
sudo apt install postgresql-server-dev-all
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

**Windows:**
Follow instructions at [pgvector documentation](https://github.com/pgvector/pgvector#windows)

### 3. Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database
CREATE DATABASE document_vectors;

# Exit psql
\q
```

### 4. Install Python Dependencies

```bash
# Clone the repository (or navigate to the project directory)
cd doc-embedding-indexer

# Install required packages
pip install -r requirements.txt
```

## Configuration

### 1. Set Up Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
# Google Gemini API Key
GEMINI_API_KEY=your_actual_gemini_api_key_here

# PostgreSQL Connection URL
POSTGRES_URL=postgresql://username:password@localhost:5432/document_vectors
```

**Getting a Gemini API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key to your `.env` file

### 2. Initialize Database Schema

Run the schema file to create the necessary table and indexes:

```bash
psql -d document_vectors -f schema.sql
```

This creates:
- The `document_chunks` table with vector support
- Indexes for efficient querying

## Usage

### Basic Usage

Index a PDF file with the default fixed-size chunking strategy:

```bash
python index_documents.py document.pdf
```

### Specify Chunking Strategy

**Fixed-size chunks with overlap (default):**
```bash
python index_documents.py document.pdf -s fixed
```

**Sentence-based chunking:**
```bash
python index_documents.py document.pdf -s sentence
```

**Paragraph-based chunking:**
```bash
python index_documents.py document.docx -s paragraph
```

### Command-Line Options

```
usage: index_documents.py [-h] [-s {fixed,sentence,paragraph}] file_path

Index documents by creating embeddings and storing them in PostgreSQL

positional arguments:
  file_path             Path to the PDF or DOCX file to process

optional arguments:
  -h, --help            show this help message and exit
  -s {fixed,sentence,paragraph}, --strategy {fixed,sentence,paragraph}
                        Text chunking strategy (default: fixed)
```

## Example Workflow

```bash
# 1. Process a PDF with sentence-based chunking
python index_documents.py reports/annual_report.pdf -s sentence

# Output:
# Processing file: reports/annual_report.pdf
# Extracting text...
# Text extracted successfully (15234 characters)
# Chunking text using 'sentence' strategy...
# Created 87 chunks
# Generating embeddings...
# Generated 87 embeddings
# Storing in database...
# Successfully indexed 87 chunks from annual_report.pdf

# 2. Process a DOCX with paragraph-based chunking
python index_documents.py notes/meeting_notes.docx -s paragraph

# 3. Check database
psql -d document_vectors -c "SELECT filename, split_strategy, COUNT(*) FROM document_chunks GROUP BY filename, split_strategy;"
```

## Database Schema

```sql
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    chunk_text TEXT NOT NULL,
    embedding vector(768),
    filename VARCHAR(255) NOT NULL,
    split_strategy VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Chunking Strategies Explained

### Fixed-Size (default)
- Splits text into chunks of 500 characters
- 50-character overlap between chunks
- Good for general-purpose use

### Sentence-Based
- Splits text by sentence boundaries (. ! ?)
- Each chunk is a complete sentence
- Good for semantic coherence

### Paragraph-Based
- Splits text by paragraphs (double newlines)
- Preserves logical document structure
- Good for documents with clear paragraph divisions

## Troubleshooting

### "GEMINI_API_KEY not found in environment variables"
- Ensure `.env` file exists in the project directory
- Verify the API key is set correctly in `.env`

### "POSTGRES_URL not found in environment variables"
- Check that `.env` contains the correct PostgreSQL connection string
- Verify database name, username, and password are correct

### "psycopg2.errors.UndefinedObject: type 'vector' does not exist"
- pgvector extension is not installed
- Run: `CREATE EXTENSION vector;` in your PostgreSQL database

### "No text extracted from the file"
- File may be corrupted or empty
- For PDFs, ensure they contain text (not just images)

## Project Structure

```
doc-embedding-indexer/
├── index_documents.py   # Main script with all functionality
├── requirements.txt     # Python dependencies
├── schema.sql          # Database schema
├── .env.example        # Environment variables template
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

