# Ossetian Dictionary Search API

A FastAPI-based search engine for Ossetian dictionaries with advanced transliteration support and typo tolerance.

## Features

- **Unified Search Endpoint**: Single `/search-html` endpoint that accepts both GET and POST requests
- **Multilingual Support**: Search in English, Russian, and Ossetian with typo tolerance
- **Advanced Transliteration**: Academic-grade transliteration between Latin and Cyrillic scripts for Ossetian terms
- **Typo Tolerance**: Multi-layered approach to handle spelling variations and common errors
- **Contextual Results**: Three levels of result context to fit different research needs
- **Source Filtering**: Ability to search within specific dictionaries
- **Comprehensive Dictionary Collection**: Access to 16 dictionaries covering historical, etymological, and specialized content
- **OpenAPI Documentation**: Full documentation with usage examples and character mappings

## API Usage

The API provides a simplified interface for search queries:

### GET /search-html/{query}

```
GET /search-html/тæрхъус
```

Parameters:
- `query`: The search term as part of the path (required)
- `limit`: Maximum number of results (optional, default: 10, max: 50)
- `transliteration`: Enable/disable transliteration (optional, default: true)
- `context_size`: Amount of context to return (optional, default: "default", options: "default", "expanded", "full")
- `source`: Filter results by source dictionary (optional)

Examples with optional parameters:
```
GET /search-html/тæрхъус?limit=5
GET /search-html/тæрхъус?transliteration=false
GET /search-html/тæрхъус?context_size=expanded
GET /search-html/тæрхъус?source=Абаев
```

The API also supports query parameters for backward compatibility:

```
GET /search-html?query=тæрхъус
```

### POST /search-html

```
POST /search-html
Content-Type: application/json

{
  "query": "тæрхъус"
}
```

The POST method is recommended for complex queries and non-ASCII characters.

Examples with optional parameters:
```json
{
  "query": "тæрхъус",
  "limit": 5
}
```

```json
{
  "query": "тæрхъус",
  "transliteration": false
}
```

```json
{
  "query": "тæрхъус",
  "context_size": "expanded",
  "source": "Толковый словарь"
}
```

### GET /health

The API provides a health check endpoint to verify the operational status of both the API and the search engine:

```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "message": "API and search engine are operational"
}
```

If the search engine is unavailable, the endpoint returns a 503 Service Unavailable status code.

## Transliteration Support

The API implements a sophisticated transliteration system between Latin and Cyrillic scripts for Ossetian terms. This means you can search for terms like "тæрхъус" or "tærqūs" and find relevant results regardless of which script was used in the original dictionary.

### Scholarly Transcription System

The system supports academic-grade transliteration conventions:
- Both æ and ä forms are recognized (æ is transcribed as ä in some scholarly works)
- Glottal stops marked with apostrophes (k', p', t', c')
- Specialized notation for labialized velar consonants (хъуыд/kẜyd, гъуыр/gẜyr, къуым/k'ẜym)
- Support for specialized characters like ә for Cyrillic у
- Indo-European palatalized sounds represented as ḱ, ǵ

### Typo Tolerance

The system includes multi-layered typo tolerance:

1. **Character Variant Generation**: Automatically creates common spelling variants
   - æ/ä → a, e
   - ū → u
   - š → sh
   - And more...

2. **Bidirectional Script Conversion**: Searches in either script find matches in both

3. **Special Case Handling**: Words with irregular transliterations have explicit mappings

4. **Meilisearch Engine**: Built-in tolerance for character transpositions, missing/extra letters

Transliteration is enabled by default but can be disabled by setting the `transliteration` parameter to `false`.

## Available Dictionaries

The search covers 16 dictionaries from the following categories:

### ИСТОРИКО-ЭТИМОЛОГИЧЕСКИЙ СЛОВАРЬ ОСЕТИНСКОГО ЯЗЫКА by В.И.АБАЕВ
- ТОМ 1 (A-K) - 1958
- ТОМ 2 (L-R) - 1973
- ТОМ 3 (S-T) - 1979
- ТОМ 4 (U-Z) - 1989

### Толковые словари
- Толковый словарь осетинского языка, Том 1 (ред. Габараев Н.Я.) - 2007
- Толковый словарь осетинского языка, Том 2 (ред. Габараев Н.Я.) - 2010

### Словари пословиц и поговорок
- Осетинские пословицы и поговорки - 1976, 1977
- Осетинские пословицы и поговорки (Айларов И.Х.) - 2006
- Осетинские дигорские народные изречения - 2011

### Специализированные словари
- Названия растений в осетинском языке (Техов Ф.Д.) - 1979
- Лексика народной медицины осетин (Дзабиев З.Т.) - 1981
- Народная медицинская терминология осетин (Джабиев З.П.) - 2018
- Краткий словарь литературных терминов - 1971
- Происхождение фамилий Дигорского ущелья (Гецати А.А.) - 1999
- Осетинские фамилии (Гаглоева З.Д.) - 2017

## API Documentation

Full API documentation is available in OpenAPI format. You can view the interactive documentation by:

1. Starting the server
2. Navigating to http://htmldicts.setia.dev:8100/ in your browser

Alternatively, view the OpenAPI specification directly at `/openapi.yaml`

## Getting Started

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Start the Meilisearch server: `docker run -p 7700:7700 getmeili/meilisearch`
4. Run the API server: `uvicorn app.api.api:app --host 0.0.0.0 --port 8100 --reload`
5. Open http://htmldicts.setia.dev:8100/ in your browser to access the API documentation

## Deployment Guide

This section provides comprehensive instructions for deploying and maintaining the dictionary server in production environments.

### Docker Compose Deployment (Recommended)

The recommended way to deploy this service is using Docker Compose, which manages both the application and Meilisearch in a containerized environment.

#### Prerequisites
- Docker and Docker Compose installed on your system
- The repository cloned to your server

#### Deployment Steps

1. Start the services:
   ```bash
   docker-compose up -d
   ```
   This command starts both the application server and Meilisearch in the background.

2. Index the dictionaries (first-time setup or reindexing):
   ```bash
   # Make the script executable
   chmod +x index-with-docker.sh
   
   # Run the indexing script
   ./index-with-docker.sh
   ```

3. Access the API:
   - API endpoints are available at `http://localhost:8100/`
   - Meilisearch admin interface is available at `http://localhost:7700/`

#### Managing the Deployment

- View logs:
  ```bash
  docker-compose logs -f app      # Application logs
  docker-compose logs -f meilisearch  # Meilisearch logs
  ```

- Stop the services:
  ```bash
  docker-compose down
  ```

- Restart the services:
  ```bash
  docker-compose restart
  ```

- Rebuild and restart (after code changes):
  ```bash
  docker-compose up -d --build
  ```

### Manual Deployment

Alternatively, you can run the components manually:

#### Running the Server

The server can be run using one of the following methods:

#### Method 1: Using the run_server.py script

```bash
python run_server.py
```

This script starts the server at `http://0.0.0.0:8000` by default.

#### Method 2: Using Uvicorn directly

```bash
uvicorn app.api.api:app --host 0.0.0.0 --port 8100
```

For production deployments, consider:
- Adding `--workers` parameter to specify the number of worker processes (e.g., `--workers 4`)
- Removing the `--reload` flag used during development
- Setting up a process manager like Supervisor or systemd to ensure the server restarts automatically

### Indexing Dictionaries

#### Initial Indexing

To index dictionaries for the first time:

1. Ensure Meilisearch is running on the default port (7700): 
   ```bash
   docker run -d --name meilisearch -p 7700:7700 -v $(pwd)/meili_data:/meili_data getmeili/meilisearch
   ```

2. Run the indexer script:
   ```bash
   python run_indexer.py
   ```

This will scan the `Dicts/` directory for HTML dictionary files and index them into Meilisearch. The process may take several minutes depending on the number and size of dictionaries.

#### Reindexing Dictionaries

To reindex dictionaries (e.g., after adding new dictionaries or updating existing ones):

1. Verify that Meilisearch is running:
   ```bash
   curl http://localhost:7700/health
   ```

2. Run the indexer script:
   ```bash
   python run_indexer.py
   ```

The indexer will automatically handle the process of updating the search index with any new or modified content.

### Production Considerations

For production deployments, consider the following:

1. **Persistent Meilisearch data**: Use volumes to persist Meilisearch data across container restarts:
   ```bash
   docker run -d --name meilisearch -p 7700:7700 -v $(pwd)/meili_data:/meili_data getmeili/meilisearch
   ```

2. **API Key Security**: Configure Meilisearch with API keys for production use:
   ```bash
   docker run -d --name meilisearch -p 7700:7700 -v $(pwd)/meili_data:/meili_data -e MEILI_MASTER_KEY=YOUR_MASTER_KEY getmeili/meilisearch
   ```

3. **HTTPS**: Use a reverse proxy like Nginx or Traefik to handle HTTPS termination and secure your API.

4. **Logging**: Configure logging for both the FastAPI application and Meilisearch to ensure you can troubleshoot issues.

5. **Monitoring**: Set up health checks to monitor the status of both the API and Meilisearch.

## Example Python Client

A sample Python client is provided in `client_example.py` to demonstrate how to use the API. Run it with:

```bash
python client_example.py "тæрхъус"
```

Additional options:
- `--method get|post|both`: Choose the HTTP method (default: both)
- `--limit N`: Set maximum number of results (default: 5)
- `--no-transliteration`: Disable transliteration
- `--health`: Check API health status 

### Context Size Options

The API provides three levels of context for search results:

1. **default**: Shows only the entry definition with no additional context
2. **expanded**: Includes approximately 2 paragraphs before and after the definition, providing additional context
3. **full**: Returns approximately 5 paragraphs before and after the definition, showing a more complete section of the dictionary

This feature is particularly useful for scholarly research where understanding the surrounding context of a dictionary entry is important.

### Source Filtering

You can filter results to come from a specific dictionary by using the `source` parameter. The value is matched against the dictionary filename, so you can use partial names like "Абаев" to match any of Abayev's dictionaries or the full filename to target a specific dictionary.

Example:
```
GET /search-html/хуым?source=ИСТОРИКО-ЭТИМОЛОГИЧЕСКИЙ СЛОВАРЬ ОСЕТИНСКОГО ЯЗЫКА - ТОМ 4
```

### Typo Tolerance

The system includes multi-layered typo tolerance:

1. **Character Variant Generation**: Automatically creates common spelling variants
   - æ/ä → a, e
   - ū → u
   - š → sh
   - And more...

2. **Bidirectional Script Conversion**: Searches in either script find matches in both

3. **Special Case Handling**: Words with irregular transliterations have explicit mappings

4. **Meilisearch Engine**: Built-in tolerance for character transpositions, missing/extra letters

Transliteration is enabled by default but can be disabled by setting the `transliteration` parameter to `false`. 