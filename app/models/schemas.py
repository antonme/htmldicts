from pydantic import BaseModel, Field
from typing import List, Optional

class SearchResult(BaseModel):
    """Individual search result from the dictionary."""
    term: str = Field(..., description="The headword or term from the dictionary")
    definition: str = Field(..., description="The full definition or explanation of the term")
    expanded_context: Optional[str] = Field(None, description="Extended context around the term, showing more of the dictionary content")
    score: float = Field(..., description="Relevance score from 0.0 to 1.0, where 1.0 is most relevant")
    source: str = Field(..., description="The dictionary source file name")

class SearchResponse(BaseModel):
    """Response model for search queries."""
    query: str = Field(..., description="The original search query")
    total_hits: int = Field(..., description="Total number of matching results found")
    processing_time_ms: int = Field(..., description="Time taken to process the query in milliseconds")
    context_size: str = Field("default", description="Size of context provided: 'default', 'expanded', or 'full'")
    results: List[SearchResult] = Field(..., description="List of matching search results")

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details if available") 