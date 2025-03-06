#!/bin/bash
# This script runs the indexer using the Docker Compose setup

# Ensure Docker Compose is running
docker-compose up -d

# Run the indexer in the app container
docker-compose exec app python run_indexer.py

echo "Indexing complete!" 