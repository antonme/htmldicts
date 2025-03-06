"""
Test that Meilisearch connection works correctly
"""
import pytest
from app.api.search_client import client, health_check

def test_meilisearch_connection():
    """Test that we can connect to Meilisearch"""
    # Check if Meilisearch is running
    try:
        health = client.health()
        assert health.get('status') == 'available'
        print("Meilisearch is running")
    except Exception as e:
        pytest.fail(f"Failed to connect to Meilisearch: {str(e)}")

def test_health_check():
    """Test the health check function"""
    # This should return True if Meilisearch is running and False otherwise
    result = health_check()
    # We expect Meilisearch to be running
    assert result is True

if __name__ == "__main__":
    test_meilisearch_connection()
    test_health_check()
    print("All Meilisearch connection tests passed!") 