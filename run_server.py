#!/usr/bin/env python
"""
Dictionary Search Server
Start the OpenAPI server for searching dictionary entries.
"""
import uvicorn

if __name__ == "__main__":
    print("Starting Dictionary Search API...")
    uvicorn.run("app.api.api:app", host="0.0.0.0", port=8100, workers=1) 
