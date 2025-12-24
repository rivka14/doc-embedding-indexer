"""
Configuration file for document embedding indexer.

This file contains application settings that define the behavior of the indexer.
For environment-specific settings (database URLs, API keys), see .env file.
"""

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
SENTENCE_SPLIT_PATTERN = r'(?<=[.!?])\s+'
PARAGRAPH_SPLIT_PATTERN = r'\n\s*\n'

DEFAULT_LOCATION = "us-central1"
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIMENSION = 768

VALID_STRATEGIES = ("fixed", "sentence", "paragraph")
