import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Meilisearch configuration
MEILISEARCH_HOST = os.getenv('MEILISEARCH_HOST', 'http://localhost:7700')
MEILISEARCH_API_KEY = os.getenv('MEILISEARCH_API_KEY', 'masterKey')
MEILISEARCH_INDEX_NAME = os.getenv('MEILISEARCH_INDEX_NAME', 'dictionary')

# API configuration
API_TITLE = "Dictionary Search API"
API_DESCRIPTION = """
OpenAPI-compliant dictionary search server supporting English, Russian, and Ossetian.
This API provides full-text search with typo tolerance in a collection of dictionaries.

## Transliteration Support
The API includes automatic transliteration between Latin and Cyrillic scripts for Ossetian terms.
This means you can search for terms like "tærqūs" or "тæрхъус" and find relevant results regardless
of which script was used in the original dictionary entries.

You can control this feature using the `transliteration` parameter in all search endpoints.
"""
API_VERSION = "1.0.0"

# Directory containing the dictionary HTML files
DICTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Dicts") 