import uvicorn
from api.api import app
from api.search_client import health_check

def main():
    """
    Main entry point for the dictionary search API.
    """
    # Check if the search engine is available
    if not health_check():
        print("WARNING: Meilisearch is not available or the index is not created.")
        print("Please make sure Meilisearch is running and run the indexer before using the API.")

if __name__ == "__main__":
    main()
    # Run the API with a single worker as requested (for low load local usage)
    uvicorn.run("app.api.api:app", host="0.0.0.0", port=8000, workers=1) 