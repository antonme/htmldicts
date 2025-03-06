from fastapi import FastAPI, Query, HTTPException, Depends, status, Body, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from typing import List, Optional
import json
import time

from ..models.schemas import SearchResponse, SearchResult, ErrorResponse
from ..models.config import API_TITLE, API_DESCRIPTION, API_VERSION
from .search_client import search_dictionary, health_check

# Create FastAPI application with OpenAPI metadata
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error"
        }
    }
)

# Add CORS middleware to allow cross-origin requests (helpful for API usage)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Add exception handlers for better handling of Unicode in error responses
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors with proper Unicode encoding"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"error": "Validation error", "detail": str(exc)}),
    )

@app.exception_handler(json.JSONDecodeError)
async def json_decode_exception_handler(request, exc):
    """Handle JSON decode errors that might happen with Unicode characters"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"error": "Invalid JSON", "detail": str(exc)}),
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with proper encoding"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder({"error": "Server error", "detail": str(exc)}),
    )

# Define search endpoint
@app.get(
    "/search-html",
    response_model=SearchResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Bad request"
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Search engine unavailable"
        }
    },
    summary="Unified search endpoint",
    description="""
    Search endpoint that accepts a query parameter and returns dictionary entries matching the query.
    Supports English, Russian, and Ossetian queries. Works with both GET and POST methods.
    
    Transliteration between Latin and Cyrillic scripts for Ossetian terms is enabled by default,
    allowing you to find matches regardless of which script is used.
    
    The context_size parameter allows you to control how much context is returned:
    - 'default': Shows just the entry definition
    - 'expanded': Shows more surrounding text for better context
    - 'full': Attempts to return the whole relevant section of the dictionary
    """
)
async def search(
    query: str = Query(..., description="Search query (term or phrase, supports English, Russian, and Ossetian)"),
    limit: int = Query(50, ge=1, le=50, description="Maximum number of results to return (1-50)"),
    limit_per_source: int = Query(5, ge=1, le=50, description="Maximum number of results to return per dictionary source"),
    transliteration: bool = Query(True, description="Enable transliteration between Latin and Cyrillic scripts for Ossetian terms"),
    context_size: str = Query("default", description="Size of context to return: 'default', 'expanded', or 'full'"),
    source: str = Query(None, description="Filter results by dictionary source (filename or part of it)")
):
    # Ensure Meilisearch is available
    if not health_check():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Search engine is unavailable", "detail": "Meilisearch service is not responding"}
        )
    
    # Validate context_size
    valid_context_sizes = ["default", "expanded", "full"]
    if context_size not in valid_context_sizes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid context size", "detail": f"Context size must be one of: {', '.join(valid_context_sizes)}"}
        )
    
    try:
        # Perform search with transliteration option
        result = search_dictionary(query, limit, limit_per_source, use_transliteration=transliteration, context_size=context_size, source=source)
        
        # Extract and format results
        hits = result.get("hits", [])
        results_list = []
        
        for hit in hits:
            result_item = SearchResult(
                term=hit.get("term", ""),
                definition=hit.get("definition", ""),
                score=hit.get("_rankingScore", 0.0),
                source=hit.get("source", "")
            )
            
            # Add expanded context if available
            if "expanded_context" in hit and hit["expanded_context"]:
                result_item.expanded_context = hit["expanded_context"]
                
            results_list.append(result_item)
        
        # Create response
        response = SearchResponse(
            query=query,
            total_hits=result.get("estimatedTotalHits", len(hits)),
            processing_time_ms=result.get("processingTimeMs", 0),
            context_size=context_size,
            results=results_list
        )
        
        # Return response as JSONResponse to ensure proper encoding
        return JSONResponse(content=jsonable_encoder(response))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Search failed", "detail": str(e)}
        )

# Add a POST endpoint for search with JSON body for better Unicode handling
@app.post(
    "/search-html",
    response_model=SearchResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Bad request"
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Search engine unavailable"
        }
    },
    summary="Unified search endpoint (POST method)",
    description="""
    POST version of the search endpoint that accepts a JSON body with the query.
    This is the most reliable way to handle non-ASCII characters.
    Supports English, Russian, and Ossetian queries.
    
    Transliteration between Latin and Cyrillic scripts for Ossetian terms is enabled by default,
    allowing you to find matches regardless of which script is used.
    
    The context_size parameter allows you to control how much context is returned:
    - 'default': Shows just the entry definition
    - 'expanded': Shows more surrounding text for better context
    - 'full': Attempts to return the whole relevant section of the dictionary
    """
)
async def search_post(
    query: str = Body(..., embed=True, description="Search query (term or phrase, supports English, Russian, and Ossetian)"),
    limit: int = Body(50, embed=True, description="Maximum number of results to return (1-50)"),
    limit_per_source: int = Body(5, embed=True, description="Maximum number of results to return per dictionary source"),
    transliteration: bool = Body(True, embed=True, description="Enable transliteration between Latin and Cyrillic scripts for Ossetian terms"),
    context_size: str = Body("default", embed=True, description="Size of context to return: 'default', 'expanded', or 'full'"),
    source: str = Body(None, embed=True, description="Filter results by dictionary source (filename or part of it)")
):
    # Ensure Meilisearch is available
    if not health_check():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Service unavailable", "detail": "Search engine is not responding"}
        )
    
    # Validate limit
    if limit < 1 or limit > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid limit", "detail": "Limit must be between 1 and 50"}
        )
    
    # Validate context_size
    valid_context_sizes = ["default", "expanded", "full"]
    if context_size not in valid_context_sizes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid context size", "detail": f"Context size must be one of: {', '.join(valid_context_sizes)}"}
        )
    
    try:
        # Perform search with transliteration option
        result = search_dictionary(query, limit, limit_per_source, use_transliteration=transliteration, context_size=context_size, source=source)
        
        # Extract and format results
        hits = result.get("hits", [])
        results_list = []
        
        for hit in hits:
            result_item = SearchResult(
                term=hit.get("term", ""),
                definition=hit.get("definition", ""),
                score=hit.get("_rankingScore", 0.0),
                source=hit.get("source", "")
            )
            
            # Add expanded context if available
            if "expanded_context" in hit and hit["expanded_context"]:
                result_item.expanded_context = hit["expanded_context"]
                
            results_list.append(result_item)
        
        # Create response
        response = SearchResponse(
            query=query,
            total_hits=result.get("estimatedTotalHits", len(hits)),
            processing_time_ms=result.get("processingTimeMs", 0),
            context_size=context_size,
            results=results_list
        )
        
        # Return response as JSONResponse to ensure proper encoding
        return JSONResponse(content=jsonable_encoder(response))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Search failed", "detail": str(e)}
        )

# Add path parameter endpoint for search
@app.get(
    "/search-html/{query}",
    response_model=SearchResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Bad request"
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Search engine unavailable"
        }
    },
    summary="Search with path parameter",
    description="""
    Search endpoint that accepts the query as a path parameter and returns dictionary entries matching the query.
    Supports English, Russian, and Ossetian queries.
    
    Transliteration between Latin and Cyrillic scripts for Ossetian terms is enabled by default,
    allowing you to find matches regardless of which script is used.
    
    The context_size parameter allows you to control how much context is returned:
    - 'default': Shows just the entry definition
    - 'expanded': Shows more surrounding text for better context
    - 'full': Attempts to return the whole relevant section of the dictionary
    """
)
async def search_path(
    query: str = Path(..., description="Search query (term or phrase, supports English, Russian, and Ossetian)"),
    limit: int = Query(50, ge=1, le=50, description="Maximum number of results to return (1-50)"),
    limit_per_source: int = Query(5, ge=1, le=50, description="Maximum number of results to return per dictionary source"),
    transliteration: bool = Query(True, description="Enable transliteration between Latin and Cyrillic scripts for Ossetian terms"),
    context_size: str = Query("default", description="Size of context to return: 'default', 'expanded', or 'full'"),
    source: str = Query(None, description="Filter results by dictionary source (filename or part of it)")
):
    # Ensure Meilisearch is available
    if not health_check():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Search engine is unavailable", "detail": "Meilisearch service is not responding"}
        )

    # Validate input
    if not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Bad request", "detail": "Search query cannot be empty"}
        )
    
    if limit < 1 or limit > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Bad request", "detail": "Limit must be between 1 and 50"}
        )
    
    # Validate context_size
    valid_context_sizes = ["default", "expanded", "full"]
    if context_size not in valid_context_sizes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid context size", "detail": f"Context size must be one of: {', '.join(valid_context_sizes)}"}
        )
    
    # Perform search with transliteration if enabled
    start_time = time.time()
    result = search_dictionary(query, limit, limit_per_source, use_transliteration=transliteration, context_size=context_size, source=source)
    end_time = time.time()
    
    # Calculate processing time in milliseconds
    processing_time_ms = int((end_time - start_time) * 1000)
    
    # Print debug information
    print(f"Search path query: {query}, limit: {limit}")
    print(f"Raw search result: {result}")
    
    # Extract and format results
    hits = result.get("hits", [])
    results_list = []
    
    print(f"Hits count: {len(hits)}")
    
    for hit in hits:
        result_item = SearchResult(
            term=hit.get("term", ""),
            definition=hit.get("definition", ""),
            score=hit.get("_rankingScore", 0.0),
            source=hit.get("source", "")
        )
        
        # Add expanded context if available
        if "expanded_context" in hit and hit["expanded_context"]:
            result_item.expanded_context = hit["expanded_context"]
            
        results_list.append(result_item)
    
    print(f"Results list count: {len(results_list)}")
    
    # Create response
    response = SearchResponse(
        query=query,
        total_hits=result.get("estimatedTotalHits", len(hits)),
        processing_time_ms=result.get("processingTimeMs", processing_time_ms),
        context_size=context_size,
        results=results_list
    )
    
    print(f"Final response: {jsonable_encoder(response)}")
    
    # Return response as JSONResponse to ensure proper encoding
    return JSONResponse(content=jsonable_encoder(response))

# Health check endpoint to verify API and search engine status
@app.get(
    "/health",
    summary="API Health Check",
    description="Check if the API and search engine are operational"
)
async def api_health_check():
    if health_check():
        return {"status": "healthy", "message": "API and search engine are operational"}
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Service unavailable", "detail": "Search engine is not responding"}
        ) 