"""
Test API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.api.api import app

client = TestClient(app)

def test_health_endpoint():
    """Test the health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "api" in data
    assert "search_engine" in data
    assert data["api"] == "running"

def test_search_endpoint_parameter_validation():
    """Test search endpoint parameter validation"""
    # Test missing query parameter
    response = client.get("/search")
    assert response.status_code == 422  # Unprocessable Entity due to missing required parameter
    
    # Test empty query parameter
    response = client.get("/search?q=")
    assert response.status_code == 422  # Unprocessable Entity due to minimum length constraint
    
    # Test invalid limit parameter
    response = client.get("/search?q=test&limit=0")
    assert response.status_code == 422  # Unprocessable Entity due to limit < 1
    
    response = client.get("/search?q=test&limit=51")
    assert response.status_code == 422  # Unprocessable Entity due to limit > 50

def test_search_endpoint_with_valid_parameters():
    """Test search endpoint with valid parameters"""
    # Note: This test assumes Meilisearch is running and has been indexed
    response = client.get("/search?q=test")
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "query" in data
    assert "total_hits" in data
    assert "processing_time_ms" in data
    assert "results" in data
    
    # Check that query is echoed back
    assert data["query"] == "test"
    
    # Check result structure if there are any results
    if data["results"]:
        first_result = data["results"][0]
        assert "term" in first_result
        assert "definition" in first_result
        assert "score" in first_result
        assert "source" in first_result

def test_search_endpoint_with_multilingual_query():
    """Test search endpoint with queries in different languages"""
    # Test English
    response = client.get("/search?q=tree")
    assert response.status_code == 200
    
    # Test Russian
    response = client.get("/search?q=лес")
    assert response.status_code == 200
    
    # Test Ossetian
    response = client.get("/search?q=хъæд")
    assert response.status_code == 200
    
    # Note: We're only checking HTTP status here
    # Actual content depends on indexed data

if __name__ == "__main__":
    test_health_endpoint()
    test_search_endpoint_parameter_validation()
    test_search_endpoint_with_valid_parameters()
    test_search_endpoint_with_multilingual_query()
    print("All API tests passed!")