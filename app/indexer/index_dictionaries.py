import os
import glob
import time
from meilisearch import Client
from .html_processor import process_html_file
from ..models.config import (
    MEILISEARCH_HOST, 
    MEILISEARCH_API_KEY,
    MEILISEARCH_INDEX_NAME,
    DICTS_DIR
)

def setup_index(client):
    """
    Set up the Meilisearch index with appropriate settings.
    
    Args:
        client: Meilisearch client
    """
    # Check if index exists or create it
    try:
        client.get_index(MEILISEARCH_INDEX_NAME)
        print(f"Using existing index: {MEILISEARCH_INDEX_NAME}")
    except Exception:
        print(f"Creating new index: {MEILISEARCH_INDEX_NAME}")
        task = client.create_index(MEILISEARCH_INDEX_NAME, {"primaryKey": "id"})
        client.wait_for_task(task.task_uid)
        print(f"Index created: {MEILISEARCH_INDEX_NAME}")
    
    # Get index
    index = client.index(MEILISEARCH_INDEX_NAME)
    
    # Make sure to delete any existing documents if we're re-indexing
    task = index.delete_all_documents()
    client.wait_for_task(task.task_uid)
    print("Deleted any existing documents to ensure clean re-indexing")
    
    # Configure index settings for multilingual search
    index_settings = {
        # Set term as highest priority for searching, then definition
        "searchableAttributes": ["term", "definition"],
        # Configure ranking rules (default is good, but we make it explicit)
        "rankingRules": [
            "words",
            "typo",
            "proximity",
            "attribute",
            "exactness"
        ],
        # Configure typo tolerance (default: 2)
        "typoTolerance": {
            "enabled": True,
            "minWordSizeForTypos": {
                "oneTypo": 4,    # Allow 1 typo for words ≥ 4 chars 
                "twoTypos": 8    # Allow 2 typos for words ≥ 8 chars
            },
            "disableOnWords": []
        }
    }
    
    # Update index settings
    task = index.update_settings(index_settings)
    print(f"Index settings updated: Task ID {task.task_uid}")
    
    # Wait for settings to be applied
    client.wait_for_task(task.task_uid)
    
    return index

def index_dictionaries():
    """
    Index all dictionary HTML files into Meilisearch.
    """
    print(f"Connecting to Meilisearch at {MEILISEARCH_HOST}")
    client = Client(MEILISEARCH_HOST, MEILISEARCH_API_KEY)
    
    # Setup index
    index = setup_index(client)
    
    # Process all HTML files in the dictionaries directory
    html_files = glob.glob(os.path.join(DICTS_DIR, "*.html"))
    
    if not html_files:
        print(f"No HTML files found in {DICTS_DIR}")
        return
    
    total_entries = 0
    for file_path in html_files:
        file_name = os.path.basename(file_path)
        print(f"Processing {file_name}...")
        
        # Process HTML file
        entries = process_html_file(file_path)
        
        if not entries:
            print(f"No entries found in {file_name}")
            continue
        
        # Index in batches
        batch_size = 1000
        for i in range(0, len(entries), batch_size):
            batch = entries[i:i+batch_size]
            task = index.add_documents(batch)
            print(f"Indexed batch {i//batch_size + 1} from {file_name}: Task ID {task.task_uid}")
            
            # Wait for indexing to complete to avoid overwhelming the server
            client.wait_for_task(task.task_uid)
        
        total_entries += len(entries)
        print(f"Indexed {len(entries)} entries from {file_name}")
    
    print(f"Indexing complete. Total entries indexed: {total_entries}")
    
    # Get index stats
    stats = client.index(MEILISEARCH_INDEX_NAME).get_stats()
    print(f"Index stats: {stats}")

if __name__ == "__main__":
    start_time = time.time()
    index_dictionaries()
    elapsed_time = time.time() - start_time
    print(f"Total indexing time: {elapsed_time:.2f} seconds") 