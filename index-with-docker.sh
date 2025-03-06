#!/bin/bash
# This script runs the indexer using the Docker Compose setup

# Ensure Docker Compose is running
docker-compose up -d

# Wait for Meilisearch to be available
echo "Waiting for Meilisearch to be ready..."
until curl -s http://localhost:7701/health > /dev/null; do
  echo "Waiting for Meilisearch..."
  sleep 2
done
echo "Meilisearch is ready!"

# Run the indexer in the app container
docker-compose exec app python run_indexer.py

echo "Indexing complete!" 