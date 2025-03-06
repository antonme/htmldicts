#!/usr/bin/env python
"""
Dictionary Indexer
Index HTML dictionary files into Meilisearch.
"""
from app.indexer.index_dictionaries import index_dictionaries

if __name__ == "__main__":
    print("Starting dictionary indexing process...")
    index_dictionaries()
    print("Indexing process complete.") 