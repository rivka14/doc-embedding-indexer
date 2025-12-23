import os
import re
import sys
import argparse
from pathlib import Path
import fitz
from docx import Document
from dotenv import load_dotenv
import google.generativeai as genai
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()


def extract_text_from_pdf(file_path):
    """Extract text from PDF file using PyMuPDF."""
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text.strip()


def extract_text_from_docx(file_path):
    """Extract text from DOCX file."""
    doc = Document(file_path)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text.strip()


def extract_text(file_path):
    """Auto-detect file type and extract text."""
    file_ext = Path(file_path).suffix.lower()

    if file_ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif file_ext == ".docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}. Only PDF and DOCX are supported.")


def chunk_fixed_size(text, chunk_size=500, overlap=50):
    """Split text into fixed-size chunks with overlap."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        start += chunk_size - overlap

    return chunks


def chunk_by_sentences(text):
    """Split text by sentences using regex."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_by_paragraphs(text):
    """Split text by paragraphs (double newlines)."""
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]


def chunk_text(text, strategy="fixed"):
    """Chunk text using the specified strategy."""
    if strategy == "fixed":
        return chunk_fixed_size(text)
    elif strategy == "sentence":
        return chunk_by_sentences(text)
    elif strategy == "paragraph":
        return chunk_by_paragraphs(text)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}. Use 'fixed', 'sentence', or 'paragraph'.")


def generate_embeddings(chunks):
    """Generate embeddings for chunks using Google Gemini API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    genai.configure(api_key=api_key)

    embeddings = []
    for chunk in chunks:
        result = genai.embed_content(
            model="models/embedding-001",
            content=chunk,
            task_type="retrieval_document"
        )
        embeddings.append(result['embedding'])

    return embeddings


def get_db_connection():
    """Create and return a PostgreSQL database connection."""
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        raise ValueError("POSTGRES_URL not found in environment variables")

    return psycopg2.connect(postgres_url)


def store_chunks(chunks, embeddings, filename, strategy):
    """Store chunks and embeddings in PostgreSQL database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    data = [
        (chunk, embedding, filename, strategy)
        for chunk, embedding in zip(chunks, embeddings)
    ]

    query = """
        INSERT INTO document_chunks (chunk_text, embedding, filename, split_strategy)
        VALUES %s
    """

    execute_values(cursor, query, data, template="(%s, %s::vector, %s, %s)")

    conn.commit()
    cursor.close()
    conn.close()


def main():
    """Main CLI function to process documents."""
    parser = argparse.ArgumentParser(
        description="Index documents by creating embeddings and storing them in PostgreSQL"
    )
    parser.add_argument(
        "file_path",
        help="Path to the PDF or DOCX file to process"
    )
    parser.add_argument(
        "-s", "--strategy",
        choices=["fixed", "sentence", "paragraph"],
        default="fixed",
        help="Text chunking strategy (default: fixed)"
    )

    args = parser.parse_args()

    try:
        print(f"Processing file: {args.file_path}")

        if not os.path.exists(args.file_path):
            print(f"Error: File not found: {args.file_path}")
            sys.exit(1)

        print("Extracting text...")
        text = extract_text(args.file_path)

        if not text:
            print("Error: No text extracted from the file")
            sys.exit(1)

        print(f"Text extracted successfully ({len(text)} characters)")

        print(f"Chunking text using '{args.strategy}' strategy...")
        chunks = chunk_text(text, strategy=args.strategy)
        print(f"Created {len(chunks)} chunks")

        print("Generating embeddings...")
        embeddings = generate_embeddings(chunks)
        print(f"Generated {len(embeddings)} embeddings")

        print("Storing in database...")
        filename = Path(args.file_path).name
        store_chunks(chunks, embeddings, filename, args.strategy)

        print(f"Successfully indexed {len(chunks)} chunks from {filename}")

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
