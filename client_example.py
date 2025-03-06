#!/usr/bin/env python3
"""
Dictionary Search API Client Example

This script demonstrates how to use the Dictionary Search API
with both GET and POST methods, as well as how to control transliteration.
"""

import requests
import json
import argparse
from urllib.parse import quote

API_BASE_URL = "http://localhost:8100"

def search_get_path(query, limit=10, transliteration=True, context_size="default", source=None):
    """
    Search the dictionary using the GET path parameter method.
    
    Args:
        query: Search term/phrase (supports English, Russian, and Ossetian)
        limit: Maximum number of results to return
        transliteration: Whether to enable transliteration for Ossetian terms
        context_size: Size of context to return ("default", "expanded", or "full")
        source: Filter results by dictionary source
        
    Returns:
        dict: API response
    """
    # URL encode the query to handle special characters
    encoded_query = quote(query)
    
    # Only include parameters that differ from defaults
    params = []
    if limit != 10:
        params.append(f"limit={limit}")
    if not transliteration:
        params.append("transliteration=false")
    if context_size != "default":
        params.append(f"context_size={context_size}")
    if source:
        params.append(f"source={quote(source)}")
    
    # Construct URL with parameters only if needed
    url = f"{API_BASE_URL}/search-html/{encoded_query}"
    if params:
        url += "?" + "&".join(params)
    
    print(f"\nGET Request with path parameter: {url}")
    response = requests.get(url)
    
    # Raise exception for HTTP errors
    response.raise_for_status()
    
    return response.json()

def search_get_query(query, limit=10, transliteration=True, context_size="default", source=None):
    """
    Search the dictionary using the GET query parameter method.
    
    Args:
        query: Search term/phrase (supports English, Russian, and Ossetian)
        limit: Maximum number of results to return
        transliteration: Whether to enable transliteration for Ossetian terms
        context_size: Size of context to return ("default", "expanded", or "full")
        source: Filter results by dictionary source
        
    Returns:
        dict: API response
    """
    # URL encode the query to handle special characters
    encoded_query = quote(query)
    
    # Start with required query parameter
    params = [f"query={encoded_query}"]
    
    # Only include parameters that differ from defaults
    if limit != 10:
        params.append(f"limit={limit}")
    if not transliteration:
        params.append("transliteration=false")
    if context_size != "default":
        params.append(f"context_size={context_size}")
    if source:
        params.append(f"source={quote(source)}")
    
    url = f"{API_BASE_URL}/search-html?{'&'.join(params)}"
    
    print(f"\nGET Request with query parameter: {url}")
    response = requests.get(url)
    
    # Raise exception for HTTP errors
    response.raise_for_status()
    
    return response.json()

def search_post(query, limit=10, transliteration=True, context_size="default", source=None):
    """
    Search the dictionary using the POST method.
    
    Args:
        query: Search term/phrase (supports English, Russian, and Ossetian)
        limit: Maximum number of results to return
        transliteration: Whether to enable transliteration for Ossetian terms
        context_size: Size of context to return ("default", "expanded", or "full")
        source: Filter results by dictionary source
        
    Returns:
        dict: API response
    """
    url = f"{API_BASE_URL}/search-html"
    headers = {"Content-Type": "application/json"}
    
    # Start with required query parameter
    payload = {"query": query}
    
    # Only include parameters that differ from defaults
    if limit != 10:
        payload["limit"] = limit
    if not transliteration:
        payload["transliteration"] = False
    if context_size != "default":
        payload["context_size"] = context_size
    if source:
        payload["source"] = source
    
    print(f"\nPOST Request to {url}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    response = requests.post(url, headers=headers, json=payload)
    
    # Raise exception for HTTP errors
    response.raise_for_status()
    
    return response.json()

def display_results(response):
    """
    Display search results in a readable format, including expanded and full contexts if available.

    Args:
        response: API response dictionary
    """
    print("\n=== Search Results ===")
    print(f"Query: {response['query']}")
    print(f"Total hits: {response['total_hits']}")
    print(f"Processing time: {response['processing_time_ms']}ms")

    if response['results']:
        print("\nResults:")
        for i, result in enumerate(response['results'], 1):
            print(f"\n{i}. {result['term']}")
            print(f"   Definition: {result['definition']}")
            if 'expanded_context' in result:
                print(f"   Expanded Context: {result['expanded_context']}")
            if 'full_context' in result:
                print(f"   Full Context: {result['full_context']}")
            print(f"   Score: {result['score']:.4f}")
            print(f"   Source: {result['source']}")
    else:
        print("\nNo results found.")

def check_health():
    """
    Check the API health status.
    
    Returns:
        bool: True if API is healthy, False otherwise
    """
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        data = response.json()
        print(f"API Health: {data['status']}")
        print(f"Message: {data['message']}")
        return data['status'] == 'healthy'
    except Exception as e:
        print(f"API Health Check Failed: {str(e)}")
        return False

def main():
    """
    Main entry point for command-line execution.
    """
    # Define argument parser
    parser = argparse.ArgumentParser(
        description="Dictionary Search API Client",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Add arguments
    parser.add_argument(
        "query",
        help="Search query (term or phrase)",
        nargs="?",
        default=None
    )
    
    parser.add_argument(
        "--method",
        help="HTTP method to use",
        choices=["get", "post", "path", "all"],
        default="all"
    )
    
    parser.add_argument(
        "--limit",
        help="Maximum number of results to return",
        type=int,
        default=5
    )
    
    parser.add_argument(
        "--no-transliteration",
        help="Disable transliteration",
        action="store_true"
    )
    
    parser.add_argument(
        "--health",
        help="Check API health",
        action="store_true"
    )
    
    parser.add_argument(
        "--context-size",
        help="Size of context to return",
        choices=["default", "expanded", "full"],
        default="default"
    )
    
    parser.add_argument(
        "--source",
        help="Filter results by dictionary source",
        default=None
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Convert no-transliteration flag to boolean
    transliteration = not args.no_transliteration
    
    # Check API health if requested
    if args.health:
        try:
            response = check_health()
            print(f"\nAPI Health: {response}")
            return
        except Exception as e:
            print(f"Health check failed: {str(e)}")
            return
    
    # Require query for search
    if not args.query:
        parser.print_help()
        print("\nError: search query is required.")
        return
    
    # Execute search based on method
    if args.method in ["get", "all"]:
        try:
            response_get = search_get_query(args.query, args.limit, transliteration, args.context_size, args.source)
            print("\n=== GET Method (Query Parameter) Results ===")
            display_results(response_get)
        except Exception as e:
            print(f"GET request failed: {str(e)}")
    
    if args.method in ["path", "all"]:
        try:
            response_path = search_get_path(args.query, args.limit, transliteration, args.context_size, args.source)
            print("\n=== GET Method (Path Parameter) Results ===")
            display_results(response_path)
        except Exception as e:
            print(f"GET (path) request failed: {str(e)}")
    
    if args.method in ["post", "all"]:
        try:
            response_post = search_post(args.query, args.limit, transliteration, args.context_size, args.source)
            print("\n=== POST Method Results ===")
            display_results(response_post)
        except Exception as e:
            print(f"POST request failed: {str(e)}")

if __name__ == "__main__":
    print("Dictionary Search API Client Example")
    print("===================================")
    main() 