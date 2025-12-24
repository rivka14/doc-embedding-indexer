import os
import re
import sys
import argparse
import logging
from pathlib import Path
import fitz
from docx import Document
from dotenv import load_dotenv
from google import genai
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('index_documents.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path):
    logger.info(f"Extracting text from PDF: {file_path}")
    text = ""
    with fitz.open(file_path) as pdf:
        logger.debug(f"PDF has {len(pdf)} pages")
        for page in pdf:
            text += page.get_text()
    logger.info(f"Extracted {len(text)} characters from PDF")
    return text.strip()


def extract_text_from_docx(file_path):
    logger.info(f"Extracting text from DOCX: {file_path}")
    doc = Document(file_path)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    logger.info(f"Extracted {len(text)} characters from DOCX")
    return text.strip()


def extract_text(file_path):
    file_ext = Path(file_path).suffix.lower()

    if file_ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif file_ext == ".docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}. Only PDF and DOCX are supported.")


def chunk_fixed_size(text, chunk_size=500, overlap=50):
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
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_by_paragraphs(text):
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]


def chunk_text(text, strategy="fixed"):
    logger.info(f"Chunking text using '{strategy}' strategy")
    if strategy == "fixed":
        chunks = chunk_fixed_size(text)
    elif strategy == "sentence":
        chunks = chunk_by_sentences(text)
    elif strategy == "paragraph":
        chunks = chunk_by_paragraphs(text)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}. Use 'fixed', 'sentence', or 'paragraph'.")
    logger.info(f"Created {len(chunks)} chunks")
    return chunks


def generate_embeddings(chunks):
    logger.info(f"Generating embeddings for {len(chunks)} chunks")
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    if not project:
        raise ValueError("GOOGLE_CLOUD_PROJECT not found in environment variables")

    logger.debug(f"Using Vertex AI project: {project}, location: {location}")
    client = genai.Client(vertexai=True, project=project, location=location)

    embeddings = []
    for i, chunk in enumerate(chunks, 1):
        logger.debug(f"Generating embedding {i}/{len(chunks)}")
        result = client.models.embed_content(
            model="text-embedding-004",
            contents=[chunk]
        )
        embeddings.append(result.embeddings[0].values)

    logger.info(f"Successfully generated {len(embeddings)} embeddings")
    return embeddings


def get_db_connection():
    logger.debug("Establishing PostgreSQL connection")
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        raise ValueError("POSTGRES_URL not found in environment variables")

    conn = psycopg2.connect(postgres_url)
    logger.debug("PostgreSQL connection established")
    return conn


def store_chunks(chunks, embeddings, filename, strategy):
    logger.info(f"Storing {len(chunks)} chunks in database for file: {filename}")
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

    logger.debug(f"Executing batch insert for {len(data)} records")
    execute_values(cursor, query, data, template="(%s, %s::vector, %s, %s)")

    conn.commit()
    logger.info(f"Successfully stored {len(chunks)} chunks in database")
    cursor.close()
    conn.close()
    logger.debug("Database connection closed")


def main():
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
        logger.info(f"Starting document indexing process for: {args.file_path}")

        if not os.path.exists(args.file_path):
            logger.error(f"File not found: {args.file_path}")
            print(f"Error: File not found: {args.file_path}")
            sys.exit(1)

        text = extract_text(args.file_path)

        if not text:
            logger.error("No text extracted from the file")
            print("Error: No text extracted from the file")
            sys.exit(1)

        chunks = chunk_text(text, strategy=args.strategy)
        embeddings = generate_embeddings(chunks)

        filename = Path(args.file_path).name
        store_chunks(chunks, embeddings, filename, args.strategy)

        logger.info(f"Successfully indexed {len(chunks)} chunks from {filename}")
        print(f"Successfully indexed {len(chunks)} chunks from {filename}")

    except ValueError as e:
        logger.error(f"ValueError: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during processing: {e}")
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
