#!/usr/bin/env python
"""
Run all tests for the Dictionary Search API
"""
import os
import sys
import pytest
import tempfile
import shutil
from meilisearch import Client

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.indexer.html_processor import process_html_file
from app.models.config import MEILISEARCH_HOST, MEILISEARCH_API_KEY, MEILISEARCH_INDEX_NAME

def setup_test_index():
    """Set up a test index with sample data"""
    print("Setting up test index...")
    
    # Initialize Meilisearch client
    client = Client(MEILISEARCH_HOST, MEILISEARCH_API_KEY)
    
    # Create test index
    test_index_name = f"{MEILISEARCH_INDEX_NAME}_test"
    index = client.index(test_index_name)
    
    # Configure index settings
    index_settings = {
        "primaryKey": "id",
        "searchableAttributes": ["term", "definition"],
        "rankingRules": [
            "words",
            "typo",
            "proximity",
            "attribute",
            "exactness"
        ],
        "typoTolerance": {
            "enabled": True,
            "minWordSizeForTypos": {
                "oneTypo": 4,
                "twoTypos": 8
            }
        }
    }
    
    # Update index settings
    task = index.update_settings(index_settings)
    client.wait_for_task(task.task_uid)
    
    # Process test sample
    sample_file = os.path.join(os.path.dirname(__file__), "test_sample.html")
    entries = process_html_file(sample_file)
    
    # Add documents to index
    if entries:
        task = index.add_documents(entries)
        client.wait_for_task(task.task_uid)
        print(f"Added {len(entries)} test documents to index")
    
    return test_index_name

def cleanup_test_index(index_name):
    """Clean up the test index"""
    print("Cleaning up test index...")
    client = Client(MEILISEARCH_HOST, MEILISEARCH_API_KEY)
    try:
        task = client.delete_index(index_name)
        client.wait_for_task(task.task_uid)
        print(f"Deleted test index {index_name}")
    except Exception as e:
        print(f"Error deleting index: {str(e)}")

def run_tests():
    """Run all tests"""
    print("Running Dictionary Search API tests...")
    
    # Try to setup a test index
    test_index_name = None
    try:
        test_index_name = setup_test_index()
    except Exception as e:
        print(f"Warning: Failed to setup test index: {str(e)}")
        print("Some tests may fail if Meilisearch is not running")
    
    # Run individual test modules directly
    test_modules = [
        "test_meilisearch_connection.py",
        "test_html_processor.py",
        "test_api.py"
    ]
    
    for test_module in test_modules:
        module_path = os.path.join(os.path.dirname(__file__), test_module)
        if os.path.exists(module_path):
            print(f"\nRunning {test_module}...")
            # Use pytest to run the test
            exit_code = pytest.main(["-xvs", module_path])
            if exit_code != 0:
                print(f"Warning: Tests in {test_module} failed with exit code {exit_code}")
        else:
            print(f"Warning: Test module {test_module} not found")
    
    # Clean up test index if created
    if test_index_name:
        cleanup_test_index(test_index_name)
    
    print("\nTests completed!")

if __name__ == "__main__":
    run_tests() 