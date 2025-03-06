from meilisearch import Client
from ..models.config import MEILISEARCH_HOST, MEILISEARCH_API_KEY, MEILISEARCH_INDEX_NAME
from transliteration import get_all_script_variants
import unicodedata

# Initialize Meilisearch client
client = Client(MEILISEARCH_HOST, MEILISEARCH_API_KEY)

def get_search_index():
    """Get the Meilisearch index for dictionaries."""
    return client.index(MEILISEARCH_INDEX_NAME)

def search_dictionary(query: str, limit: int = 50, limit_per_source: int = 5, use_transliteration: bool = True, context_size: str = "default", source: str = None):
    """
    Search the dictionary index with typo tolerance.
    
    Args:
        query: The search term(s)
        limit: Maximum number of results to return (default: 50)
        limit_per_source: Maximum number of results to return per dictionary source (default: 5)
        use_transliteration: Whether to apply transliteration (default: True)
        context_size: Size of context to return (default, expanded, full)
        source: Filter results by source dictionary (optional)
        
    Returns:
        dict: Raw Meilisearch response with merged results if transliteration is used
    """
    index = get_search_index()
    try:
        # Debug source parameter
        if source:
            print(f"DEBUG: Source parameter received: '{source}'")
        
        # Ensure query is properly encoded as Unicode for non-ASCII characters
        if query:
            # Make sure the query is a proper Python string (handles edge cases)
            query = str(query)
        
        # Get expanded results based on context_size parameter
        attributes_to_retrieve = ["term", "definition", "source", "id"]
        
        # Add appropriate context field based on requested size
        if context_size == "expanded":
            attributes_to_retrieve.append("expanded_context")
        elif context_size == "full":
            attributes_to_retrieve.append("full_context")
        
        search_params = {
            "showRankingScore": True,
            "attributesToRetrieve": attributes_to_retrieve
        }
        
        # Increase the limit if source filtering is requested to ensure we have enough results to filter
        if source:
            search_params["limit"] = 100  # Get more results to filter
        else:
            search_params["limit"] = min(100, limit * 2)  # Get enough results to apply per-source limiting
        
        if not use_transliteration:
            # Standard search without transliteration
            result = index.search(
                query,
                search_params
            )
            
            # Process results to ensure proper context field
            process_search_results(result, context_size)
            
            # Apply client-side source filtering if needed
            if source:
                print(f"DEBUG: Source filtering with '{source}', pre-filter hit count: {len(result['hits'])}")
                
                # Normalize source parameter
                source_normalized = unicodedata.normalize('NFKC', source.lower())
                
                # Simple filtering approach with normalization
                filtered_hits = []
                
                for hit in result.get("hits", []):
                    hit_source = unicodedata.normalize('NFKC', hit.get("source", "").lower())
                    if source_normalized in hit_source:
                        filtered_hits.append(hit)
                
                result["hits"] = filtered_hits
                print(f"DEBUG: Post-filter hit count: {len(result['hits'])}")
                
                # Apply limit after filtering
                result["hits"] = result["hits"][:limit]
            else:
                # Apply limit_per_source
                source_counts = {}
                filtered_hits = []
                
                for hit in result.get("hits", []):
                    hit_source = hit.get("source", "")
                    # Initialize counter for this source if not exists
                    if hit_source not in source_counts:
                        source_counts[hit_source] = 0
                    
                    # Add hit if under per-source limit
                    if source_counts[hit_source] < limit_per_source:
                        filtered_hits.append(hit)
                        source_counts[hit_source] += 1
                        
                        # Stop if we've reached the total limit
                        if len(filtered_hits) >= limit:
                            break
                
                result["hits"] = filtered_hits
            
            return result
        else:
            # Enhanced search with transliteration
            # Generate script variants for the query
            query_variants = get_all_script_variants(query)
            
            # Start with an empty result set
            merged_results = {
                "hits": [],
                "query": query,
                "processingTimeMs": 0,
                "estimatedTotalHits": 0,
            }
            
            # Search for each query variant and merge results
            seen_ids = set()  # Track IDs to avoid duplicates
            
            for variant in query_variants:
                variant_result = index.search(
                    variant,
                    search_params
                )
                
                # Update processing time (sum of all variants)
                merged_results["processingTimeMs"] += variant_result.get("processingTimeMs", 0)
                
                # Add hits that we haven't seen yet
                for hit in variant_result.get("hits", []):
                    hit_id = hit.get("id")
                    if hit_id not in seen_ids:
                        seen_ids.add(hit_id)
                        merged_results["hits"].append(hit)
                
                # Update estimated total hits to maximum across variants
                merged_results["estimatedTotalHits"] = max(
                    merged_results["estimatedTotalHits"],
                    variant_result.get("estimatedTotalHits", 0)
                )
            
            # Sort merged results by ranking score
            merged_results["hits"] = sorted(
                merged_results["hits"],
                key=lambda x: x.get("_rankingScore", 0.0),
                reverse=True
            )
            
            # Apply client-side source filtering if needed
            if source:
                print(f"DEBUG: Source filtering with '{source}', pre-filter hit count: {len(merged_results['hits'])}")
                
                # Normalize source parameter
                source_normalized = unicodedata.normalize('NFKC', source.lower())
                
                # Simple filtering approach with normalization
                filtered_hits = []
                
                for hit in merged_results.get("hits", []):
                    hit_source = unicodedata.normalize('NFKC', hit.get("source", "").lower())
                    if source_normalized in hit_source:
                        filtered_hits.append(hit)
                
                merged_results["hits"] = filtered_hits
                print(f"DEBUG: Post-filter hit count: {len(merged_results['hits'])}")
                
                # Apply limit after filtering
                merged_results["hits"] = merged_results["hits"][:limit]
            else:
                # Apply limit_per_source
                source_counts = {}
                filtered_hits = []
                
                for hit in merged_results.get("hits", []):
                    hit_source = hit.get("source", "")
                    # Initialize counter for this source if not exists
                    if hit_source not in source_counts:
                        source_counts[hit_source] = 0
                    
                    # Add hit if under per-source limit
                    if source_counts[hit_source] < limit_per_source:
                        filtered_hits.append(hit)
                        source_counts[hit_source] += 1
                        
                        # Stop if we've reached the total limit
                        if len(filtered_hits) >= limit:
                            break
                
                merged_results["hits"] = filtered_hits
            
            # Process results to ensure proper context field
            process_search_results(merged_results, context_size)
            
            return merged_results
    except Exception as e:
        # Re-raise with more context for API error handling
        print(f"Search error with query '{query}': {str(e)}")
        raise RuntimeError(f"Search engine error: {str(e)}")

def process_search_results(results, context_size):
    """
    Process search results to ensure proper context fields are available.
    
    Args:
        results: The search results dictionary
        context_size: The requested context size (default, expanded, full)
    """
    if context_size == "default":
        # Remove any context fields if present
        for hit in results.get("hits", []):
            if "expanded_context" in hit:
                del hit["expanded_context"]
            if "full_context" in hit:
                del hit["full_context"]
    elif context_size == "expanded":
        # Ensure expanded_context is available and properly named
        for hit in results.get("hits", []):
            if "expanded_context" not in hit:
                # If expanded_context isn't available, generate it
                hit["expanded_context"] = generate_expanded_context(hit.get("definition", ""), context_size)
    elif context_size == "full":
        # Ensure full_context is available and properly named
        for hit in results.get("hits", []):
            if "full_context" in hit:
                # Rename full_context to expanded_context for API consistency
                hit["expanded_context"] = hit["full_context"]
                del hit["full_context"]
            else:
                # If full_context isn't available, generate it
                hit["expanded_context"] = generate_expanded_context(hit.get("definition", ""), context_size)

def generate_expanded_context(definition: str, context_size: str) -> str:
    """
    Generate expanded context based on the definition text.
    This function creates a larger context window around the definition.
    
    Args:
        definition: The original definition text
        context_size: How much context to include (default, expanded, full)
        
    Returns:
        str: Expanded context text
    """
    if not definition or context_size == "default":
        return None
        
    # For "expanded" context, provide 2x the original text size if possible
    if context_size == "expanded":
        # In a real implementation, we would retrieve nearby entries from the original source
        # This is a simplified version that just adds a note
        additional_context = (
            "\n\n[Note: This is an expanded context view. "
            "In a complete implementation, this would show surrounding entries and more "
            "of the dictionary context. The current entry definition is shown above.]"
        )
        return definition + additional_context
        
    # For "full" context, provide much more context
    if context_size == "full":
        # In a real implementation, we would retrieve a much larger section from the original source
        additional_context = (
            "\n\n[Note: This is a full context view. "
            "In a complete implementation, this would show a large section of the dictionary "
            "surrounding this entry, potentially including multiple pages of content. "
            "The current entry definition is shown above.]"
        )
        return definition + additional_context
        
    return None

def health_check():
    """
    Check if Meilisearch is running and accessible.
    
    Returns:
        bool: True if Meilisearch is healthy, False otherwise
    """
    try:
        # First check if the Meilisearch server is running
        print(f"Checking Meilisearch health at {MEILISEARCH_HOST}")
        health = client.health()
        print(f"Meilisearch health response: {health}")
        
        if health.get('status') != 'available':
            print(f"Meilisearch is not available: {health}")
            return False
            
        # Then check if our index exists
        print(f"Checking if index {MEILISEARCH_INDEX_NAME} exists")
        indexes = client.get_indexes()
        print(f"Found indexes: {indexes}")
        
        # Index objects don't have a get method, so we need to check the uid attribute directly
        index_exists = any(index.uid == MEILISEARCH_INDEX_NAME for index in indexes.get('results', []))
        
        if not index_exists:
            print(f"Index {MEILISEARCH_INDEX_NAME} not found in Meilisearch")
            return False
            
        # Try a simple search to verify the index is working
        print("Testing a simple search")
        index = get_search_index()
        test_search = index.search("test", {"limit": 1})
        print(f"Search test results: {test_search}")
        
        return True
    except Exception as e:
        print(f"Health check failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False 