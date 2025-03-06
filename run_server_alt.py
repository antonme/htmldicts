#!/usr/bin/env python
"""
Dictionary Search Server (Alternative Port)
Start the OpenAPI server for searching dictionary entries on port 8100.
"""
import uvicorn
import os

if __name__ == "__main__":
    print("Starting Dictionary Search API on port 8100...")
    uvicorn.run("app.api.api:app", host="0.0.0.0", port=8100, workers=1) 