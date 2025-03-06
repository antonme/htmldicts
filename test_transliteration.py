#!/usr/bin/env python
"""
Test Script for Ossetian Transliteration

This script tests the transliteration module with various Ossetian terms
in both Latin and Cyrillic scripts, including scholarly notations.
"""
import requests
import json
from transliteration import latin_to_cyrillic, cyrillic_to_latin, get_all_script_variants, generate_variants

# API URL
API_URL = "http://htmldicts.setia.dev:8100"

def test_transliteration_module():
    """Test the transliteration module functions."""
    print("\n=== Testing Transliteration Module ===")
    
    # Test cases for Latin to Cyrillic conversion
    latin_test_cases = [
        ('tærqūs', 'тæрхъус'),
        ('tärqūs', 'тæрхъус'),  # Testing ä variant
        ('tærqos', 'тæрхъус'),
        ('ævsarm', 'æвсарм'),
        ('k\'ẜym', 'къуым'),    # Testing apostrophe and labialization
        ('kẜyd', 'хъуыд'),      # Testing labialization
        ('gẜyr', 'гъуыр'),      # Testing labialization
        ('ә', 'у')              # Testing ә mapping
    ]
    
    print("\nLatin to Cyrillic conversion:")
    for latin, expected_cyrillic in latin_test_cases:
        result = latin_to_cyrillic(latin)
        print(f"  {latin} -> {result}")
        print(f"  Expected: {expected_cyrillic}")
        print(f"  Correct: {result == expected_cyrillic}\n")
    
    # Test cases for Cyrillic to Latin conversion
    cyrillic_test_cases = [
        ('тæрхъус', 'tærqūs'),
        ('æвсарм', 'ævsarm'),
        ('къуым', 'k\'ẜym'),    # Testing apostrophe and labialization
        ('хъуыд', 'kẜyd'),      # Testing labialization
        ('гъуыр', 'gẜyr')       # Testing labialization
    ]
    
    print("\nCyrillic to Latin conversion:")
    for cyrillic, expected_latin in cyrillic_test_cases:
        result = cyrillic_to_latin(cyrillic)
        print(f"  {cyrillic} -> {result}")
        print(f"  Expected: {expected_latin}")
        print(f"  Correct: {result == expected_latin}\n")
    
    # Test getting all script variants
    variant_test_cases = [
        'tærqūs',
        'tärqūs',
        'тæрхъус',
        'k\'ẜym',
        'kẜyd'
    ]
    
    print("\nGenerating all script variants:")
    for term in variant_test_cases:
        variants = get_all_script_variants(term)
        print(f"  {term} -> {variants}")
        
    # Test generating spelling variants for typo tolerance
    print("\nGenerating spelling variants for typo tolerance:")
    typo_test_cases = [
        'tærqūs',
        'tärqūs',
        'kẜyd',
        'čermen'
    ]
    
    for term in typo_test_cases:
        variants = generate_variants(term)
        print(f"  {term} -> {variants}")

def test_api_search():
    """Test the API search with transliteration."""
    print("\n=== Testing API Search with Transliteration ===")
    
    # Test cases
    test_cases = [
        {'term': 'tærqūs', 'limit': 5, 'transliteration': True},
        {'term': 'тæрхъус', 'limit': 5, 'transliteration': True},
        {'term': 'tärqūs', 'limit': 5, 'transliteration': True},  # Testing ä variant
        {'term': 'k\'ẜym', 'limit': 5, 'transliteration': True},  # Testing apostrophe and labialization
        # Compare with transliteration disabled
        {'term': 'tærqūs', 'limit': 5, 'transliteration': False}
    ]
    
    for i, case in enumerate(test_cases):
        print(f"\nTest {i+1}: Search for '{case['term']}' with transliteration={case['transliteration']}")
        
        # Test with POST endpoint (most reliable for Unicode)
        post_url = f"{API_URL}/search"
        post_data = {
            'query': case['term'],
            'limit': case['limit'],
            'transliteration': case['transliteration']
        }
        
        try:
            response = requests.post(post_url, json=post_data)
            response.raise_for_status()
            results = response.json()
            
            print(f"  Query: {results['query']}")
            print(f"  Total hits: {results['total_hits']}")
            print(f"  Processing time: {results['processing_time_ms']} ms")
            print(f"  Number of results: {len(results['results'])}")
            
            # Print the top result if available
            if results['results']:
                top_result = results['results'][0]
                print(f"\n  Top result:")
                print(f"    Term: {top_result['term']}")
                print(f"    Score: {top_result['score']}")
                print(f"    Source: {top_result['source']}")
                # Only print the first 100 characters of the definition
                definition_preview = top_result['definition'][:100] + "..." if len(top_result['definition']) > 100 else top_result['definition']
                print(f"    Definition: {definition_preview}")
            
        except requests.exceptions.RequestException as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    # Test transliteration module
    test_transliteration_module()
    
    # Test API search
    test_api_search() 