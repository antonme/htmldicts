# Building an OpenAPI-Compliant Multilingual Search Server with Meilisearch

Implementing a typo-tolerant dictionary search service involves combining a fast search backend with a robust API framework. Below is a comprehensive guide covering all aspects of the project, from data ingestion to API design, ensuring support for English, Russian, and Ossetian queries. We will use **Meilisearch** as the core search engine, and a Python web framework (FastAPI) to expose an OpenAPI-compliant REST API. The guide includes best practices for performance (sub-500ms response times), relevance ranking, and AI-friendly response design.

## 1. Core Search Engine: Meilisearch

**Why Meilisearch:** Meilisearch is a modern, lightweight full-text search engine that offers **built-in typo tolerance, full-text indexing, and fast relevance-based ranking** out of the box ([
MeiliSearch: A Minimalist Full-Text Search Engine  ](https://tech.marksblogg.com/meilisearch-full-text-search.html#:~:text=lives%20as%20a%2035%20MB,and%20can%20be%20easily%20customised)). It’s designed for quick search-as-you-type experiences and is well-suited for multilingual data. Key features that make Meilisearch ideal for our use case include:

- **Typo Tolerance:** Meilisearch uses advanced algorithms (like Levenshtein Automata) to handle spelling mistakes gracefully. It precomputes word variations and can match queries with up to two typos by default ([How to deliver the best search results: inside a full text search engine](https://www.meilisearch.com/blog/how-full-text-search-engines-work#:~:text=Modern%20search%20experiences%20only%20require,of%20the%20most%20frequent%20prefixes)) ([How to deliver the best search results: inside a full text search engine](https://www.meilisearch.com/blog/how-full-text-search-engines-work#:~:text=%2A%20insertions%2C%20e.g.%20hat%20,sacred)). This means a search for “оскетия” can still find “Осетия” (Ossetia) if such variations exist in the index.
- **Relevance Ranking:** Documents are ranked using a set of default rules – in order: matching **words**, typo count, term **proximity**, field **attribute** importance, optional custom sorting, and **exactness** ([Ranking Rules Setting API | Welcome to the Meilisearch specifications!](https://specs.meilisearch.dev/specifications/text/0123-ranking-rules-setting-api.html#:~:text=Built,Proximity%3B%20Attribute%3B%20Sort%3B%20Exactness)). These rules ensure that the most relevant entries (e.g. exact matches with fewer typos) appear first.
- **Performance:** Written in Rust on top of LMDB, Meilisearch is extremely fast and compact. It can handle many queries per second with low latency, which is crucial for achieving sub-500ms response times. It also supports **prefix search** (for instant “search-as-you-type” suggestions) and scales well for our data size (~100MB).
- **Ease of Integration:** Meilisearch provides a simple **RESTful HTTP API** and official client libraries for Python. We can run Meilisearch as a separate service (e.g., via Docker or a local binary) and interact with it from our Python server. It’s essentially a drop-in search engine that we feed data and query as needed.

**Setting up Meilisearch:** To get started, download and run the Meilisearch server (a single binary or Docker image). For example, using Docker:

```bash
docker run -p 7700:7700 -d getmeili/meilisearch:latest \
  meilisearch --env development --http-addr '0.0.0.0:7700'
``` 

This will launch Meilisearch listening on port 7700. In development mode a default master key is generated (or you can specify one). In production, set a master key and use it for authenticated requests. The Python backend will communicate with Meilisearch via this HTTP API.

**Index Creation:** Once Meilisearch is running, plan for an index to store the dictionary entries. For example, we might create an index named `"dictionary"` to hold all entry documents. The index can be created via the Python client or HTTP request – if you use the Python client, it will auto-create the index when adding documents if it doesn’t exist.

## 2. Language Support for English, Russian, and Ossetian

Supporting multiple languages requires careful handling of text processing. Fortunately, Meilisearch is **designed to be multilingual**, with optimized support for any language using whitespace-separated words ([Language — Meilisearch documentation](https://www.meilisearch.com/docs/learn/resources/language#:~:text=Meilisearch%20is%20multilingual%2C%20featuring%20optimized,support%20for)). English, Russian, and Ossetian all use spaces between words (Ossetian uses the Cyrillic script, similar to Russian), so Meilisearch’s default tokenizer can index them effectively. Key considerations:

- **Character Normalization:** Meilisearch will normalize text to handle different forms of the same character. For example, it lowercases text by default and can normalize diacritics. It also recognizes Cyrillic characters, so Russian/Ossetian letters will be indexed as distinct tokens but still handled under typo tolerance (e.g., it knows the Cyrillic “а” vs Latin “a” as separate characters).
- **Stemming and Lemmatization:** Meilisearch includes basic stemming support for many languages ([
MeiliSearch: A Minimalist Full-Text Search Engine  ](https://tech.marksblogg.com/meilisearch-full-text-search.html#:~:text=lives%20as%20a%2035%20MB,and%20can%20be%20easily%20customised)). This means word variants (plurals, conjugations) may be matched to some degree. However, for languages like Russian and Ossetian, which are highly inflected, you might consider additional measures:
  - By default, Meilisearch will treat each word as a token and might not automatically reduce it to a root form. If an exact morphological stemming is needed (e.g., searching “книга” finds “книги”), consider using synonyms or an external preprocessing step. For instance, you could use a library like **pymorphy2** (for Russian) offline to generate synonyms (e.g., adding `"книга"` as a synonym of `"книги"` in index settings).
  - That said, even without explicit stemming, Meilisearch’s tolerant prefix search can often catch variants if the beginning of the word matches. Also, since our dictionary likely contains all word forms (headwords or within definitions), a query might still hit the correct entry.
- **Ossetian Language:** Ossetian uses a Cyrillic-based alphabet (with unique letters like Ӕ). Meilisearch does not have special handling for Ossetian specifically (it’s a less common language), but it will index these characters just like any other Unicode text. Ensure that the text is in Unicode (UTF-8) format when indexing so that characters like **Ӕ** are preserved. If needed, you can add custom synonyms for Ossetian orthographic variants or alternate spellings.
- **Stop Words:** By default, Meilisearch doesn’t remove stop-words unless configured. For English, common words like “the”, “and” might not be significant in search queries. For Russian, words like “и” (and), “в” (in) etc., and Ossetian equivalents could be considered stop words. If your dictionary text or queries are expected to include such filler words, you can configure the index’s stop-words list (via `index.update_settings(stopWords=[...])`). Removing them can improve result relevance. **However**, be cautious: in a dictionary, even small function words might appear in phrases or examples, so only use stop-words if you see clear benefit.
- **Typos across languages:** Meilisearch’s typo tolerance works on the character level and does not need language-specific dictionaries – it will allow up to 2 character differences for any word. This means it works for Cyrillic-based words as well. For example, a query with a mistyped Cyrillic letter will still find the correct word if the rest matches. Keep in mind that some letters between Latin and Cyrillic look similar (e.g. “A” vs “А”), so ensure the queries use the correct script. You might consider normalizing input queries by detecting the script and converting if users might input the “wrong” script by mistake (this is probably a rare edge-case).

**Language-specific indexing settings:** Meilisearch recently introduced a **`filterableAttributes`** and **`sortableAttributes`**, but more relevant for relevance is **`searchableAttributes`**. We can leverage this to improve multilingual support:
- If your dictionary entries have identifiable fields, e.g. an English headword and a Russian definition, you might index them in separate fields (like `term_en`, `definition_ru`, etc.). Then, set `searchableAttributes` order such that the most likely field for a query is searched first. For example, if queries in English are often the headword, put `term_en` before `definition_ru` in the searchable order. This way, an English query matches the headword field (higher priority) before trying to match within the Russian definition.
- If the dictionary is bilingual (say Ossetian headword with Russian definition), you can similarly separate fields. For a monolingual dictionary, you might have just one field for content or split by sub-parts of the entry.

**Synonyms for Cross-Language Queries:** If you want to allow, for example, an English query to find a Russian/Ossetian term or vice versa, synonyms can be configured. For instance, if the dictionary includes translations, you could add an index synonym such that `"water"` is a synonym of `"водa"` (Russian for water) and `"дзæр"` (Ossetian for water), so a search for one returns entries containing the others. Synonyms in Meilisearch are user-defined mappings of terms that should be considered equivalent ([Ranking Score | Welcome to the Meilisearch specifications!](https://specs.meilisearch.dev/specifications/text/0195-ranking-score.html#:~:text=ranking%20rule%20with%20a%20weight,of%20typos%20for%20a%20query)). This can enhance cross-language retrieval if needed.

In summary, Meilisearch by itself can handle our multilingual requirements. Russian is explicitly supported (issue #612 confirms Russian tokenization is built-in ([How to add Russian language suport? · Issue #612 · meilisearch/meilisearch · GitHub](https://github.com/meilisearch/MeiliSearch/issues/612#:~:text=Kerollmops%20%20%20commented%20,67))), and Ossetian will be handled as generic Unicode text. By leveraging **synonyms and careful indexing of fields**, we ensure that English, Russian, or Ossetian queries all return relevant results with typo-tolerance.

## 3. Data Handling: Loading and Indexing Dictionary HTML Files

The dictionary data consists of 50–100MB of text spread across multiple HTML files in a "Dicts" directory. We need to **extract the text content from these HTML files**, clean it, split it into searchable entries, and feed it to Meilisearch for indexing.

**Preparation – reading HTML files:** Use Python to read and parse the HTML files. The recommended approach is to use **BeautifulSoup (from bs4)** with the **lxml parser** for speed. BeautifulSoup provides a simple way to navigate and extract text from HTML, and using the lxml backend dramatically improves parsing performance ([Making beautifulsoup Parsing 10 times faster - The HFT Guy](https://thehftguy.com/2020/07/28/making-beautifulsoup-parsing-10-times-faster/#:~:text=The%20internet%20is%20unanimous%2C%20one,should%20be%20much%20much%20faster)). Install these libraries via pip: `pip install beautifulsoup4 lxml`. 

**Parsing and cleaning HTML:** Since the files are described as “pre-cleaned”, they likely contain mostly the dictionary text and minimal extraneous markup (perhaps bold terms, italic pronunciations, etc.). We should:
- **Remove HTML tags** that are not part of the meaningful content. For example, strip out `<div>` containers, navigation links, etc., if any. With BeautifulSoup, you can use `soup.get_text()` to get all text, but it might lose structure. Alternatively, navigate the HTML structure if it's consistent (for instance, if each entry is within certain tags).
- **Identify entry boundaries:** Determine how dictionary entries are structured in the HTML. Common patterns:
  - Each entry could be a `<p>` or `<div>` block, possibly with the headword in bold (`<b>` or `<strong>` tags) followed by the definition.
  - Some dictionaries use `<dt>` (definition term) and `<dd>` (definition description) within `<dl>` lists.
  - If the HTML uses specific markup for headwords (like `<b>` or an `<h3>` for each term), we can split on that.
  
  Examine a sample file manually (or use BeautifulSoup to find a tag that consistently wraps each entry). For example:
  ```python
  from bs4 import BeautifulSoup
  html = open("Dicts/sample.html", encoding="utf-8").read()
  soup = BeautifulSoup(html, "lxml")
  entries = soup.find_all("p")  # or soup.find_all("div", class_="entry") depending on structure
  ```
  If this yields one entry per item, great. If not, adjust the tag or examine the HTML structure.
- **Extract fields:** Once you can isolate each dictionary entry, break it into at least two parts for indexing: the **headword (term)** and the **definition text**. For example:
  ```python
  for entry in entries:
      term = entry.find('b').get_text()  # headword in bold
      definition_text = entry.get_text()
      # Possibly remove the term from definition_text to avoid duplication, if needed
  ```
  We now create a document for indexing, e.g., `{"id": "...", "term": term, "definition": definition_text}`.
  
  Generating a unique `"id"` for each entry is important as the primary key in Meilisearch (to avoid duplicates and allow updates). This could be a combination of file name and an index number, or even the term itself if terms are unique. Since multiple entries might have the same term (homographs), safer is file-based or a simple incremental ID.

- **Volume considerations:** 50-100MB of text is quite large (potentially hundreds of thousands of words). Ensure you run this parsing in a memory-efficient manner. Using `BeautifulSoup` on one file at a time is advisable instead of loading all files at once. For each file, parse and extract documents, then send them to Meilisearch before moving to the next file (this avoids holding the entire dataset in RAM). You can accumulate documents from one file in a list, index them, then clear the list for the next file.
- **Speed:** Using lxml parser as mentioned is one optimization ([10 Tips to Speed Up Beautiful Soup in Python Web Scraping | Medium](https://medium.com/@datajournal/how-to-make-pythons-beautiful-soup-faster-2d508660486f#:~:text=Medium%20medium,cchardet%20for%20faster%20encoding%20detection)). If parsing still becomes a bottleneck, you could consider more direct text processing (like regex) for simpler structures, but BeautifulSoup is usually fine for ~100MB split across files. Another tip is to disable unnecessary features of BeautifulSoup like verbose formatting or to use `.iterator` if available. Given this is a one-time (or infrequent) indexing operation, a few extra seconds is acceptable.

**Indexing into Meilisearch:** With the data extracted as a list of documents (each a dict with fields like id, term, definition), we use the Meilisearch Python client to load them:
1. **Initialize the client and index:** 
   ```python
   from meilisearch import Client
   client = Client("http://127.0.0.1:7700", "masterKey")  # use your actual master key
   index = client.index("dictionary")  # this will create the index if it doesn't exist
   ```
2. **Configure index settings (optional but recommended):**
   - Set the **primary key** if not already set. For example: `index.update_settings({"primaryKey": "id"})`. This ensures Meilisearch uses the `"id"` field as the unique identifier.
   - Define **searchable attributes** ordering. If we stored `term` and `definition` separately, we might want to prioritize matches in `term`. For instance:
     ```python
     index.update_settings({"searchableAttributes": ["term", "definition"]})
     ```
     By default, if not set, Meilisearch considers all fields, but defining the order helps the `attribute` ranking rule to favor the `term` field ([How can a complete novice get started using this? I want to index & search HTML files. · meilisearch meilisearch · Discussion #1881 · GitHub](https://github.com/meilisearch/meilisearch/discussions/1881#:~:text=The%20advantage%20of%20this%20second,all%20depends%20on%20your%20real)).
   - (Optional) set **stopWords**, **synonyms**, or **typoTolerance** settings. Meilisearch’s defaults for typo tolerance are usually fine, but you could tweak e.g. `minWordSizeForTypos` or allowed typos if needed. Synonyms can be added via `index.update_settings({"synonyms": {...}})` providing a dictionary of synonym groups.
   - If results should highlight matches, you could use Meilisearch’s _highlighting_ feature by specifying `attributesToHighlight` in search queries. For now, we aim for plain text output, which is simpler for an AI to consume.

3. **Batch indexing documents:** Instead of sending all data in one huge request (which could hit size limits or be slow), index in batches. Meilisearch can efficiently handle batches of documents. For example:
   ```python
   batch_size = 1000  # number of entries per batch
   documents = [] 
   for each entry in parsed_entries:
       documents.append(entry)
       if len(documents) >= batch_size:
           index.add_documents(documents)
           documents.clear()
   # after loop, add remaining
   if documents:
       index.add_documents(documents)
   ```
   This pseudo-code splits adding into chunks of 1000 entries. Adjust batch_size based on memory (e.g., 1000 entries ~ maybe a few hundred KB of JSON). The Meilisearch Python client’s `add_documents` returns a task status (in Meilisearch v1.x, indexing is asynchronous). You should wait for indexing tasks to complete to ensure all data is indexed before serving queries. The client provides methods to check task status or you can poll `client.get_task(task_uid)`.
   
   **Note:** Each dictionary entry is fairly small, but ensure no single document exceeds Meilisearch limits. As of v0.24.0+, Meilisearch can index up to 65,536 words per attribute ([How can a complete novice get started using this? I want to index & search HTML files. · meilisearch meilisearch · Discussion #1881 · GitHub](https://github.com/meilisearch/meilisearch/discussions/1881#:~:text=,65536)). By splitting entries individually, we won’t hit this limit. Avoid the approach of one document = one entire HTML file (which could exceed 65k words and fail to index some content ([How can a complete novice get started using this? I want to index & search HTML files. · meilisearch meilisearch · Discussion #1881 · GitHub](https://github.com/meilisearch/meilisearch/discussions/1881#:~:text=,65536))).

4. **Verify indexing:** After indexing, you can test a simple query directly via the client or curl:
   ```python
   result = index.search("test query")
   print(result["hits"][0:3])
   ```
   Ensure that English, Russian, and Ossetian terms appear in the index (try searching a known word from each language).

## 4. Performance Considerations (Sub-500ms Response)

Achieving a response time under 500ms is feasible with this setup, given Meilisearch’s speed and our relatively small index (100MB of text). Key performance strategies:

- **FastAPI for high-performance web API:** We will use FastAPI (with Uvicorn ASGI server) as the web framework. FastAPI is built on asynchronous Starlette and can handle many requests with very low overhead. In benchmarks, FastAPI on a single Uvicorn worker can handle **15,000+ requests per second** for simple endpoints, thanks to async concurrency ([Flask vs FastAPI: An In-Depth Framework Comparison | Better Stack Community](https://betterstack.com/community/guides/scaling-python/flask-vs-fastapi/#:~:text=FastAPI%20can%20handle%20multiple%20requests,leading%20to%20better%20resource%20utilization)). This far outperforms Flask’s WSGI-based approach (which would need multiple threads/processes to match throughput) ([Flask vs FastAPI: An In-Depth Framework Comparison | Better Stack Community](https://betterstack.com/community/guides/scaling-python/flask-vs-fastapi/#:~:text=FastAPI%20can%20handle%20multiple%20requests,leading%20to%20better%20resource%20utilization)) ([Flask vs FastAPI: An In-Depth Framework Comparison | Better Stack Community](https://betterstack.com/community/guides/scaling-python/flask-vs-fastapi/#:~:text=Real,increases%2C%20particularly%20with%20I%2FO%20operations)). For a local service with one or two threads, FastAPI provides excellent performance and will easily stay within the 500ms budget per request (most queries likely ~50ms – 100ms).
- **Minimal threads:** Running Uvicorn with one worker (single process) and leveraging async allows concurrency without multiple threads. This avoids context-switching overhead and keeps latency low. You can start Uvicorn as:
  ```bash
  uvicorn app:api --workers 1 --port 8000
  ```
  (Where `app:api` assumes your FastAPI instance is named `api` in `app.py`). With one worker, simultaneous requests are handled via asyncio – since our search function call is I/O-bound (network call to Meilisearch), FastAPI can interleave multiple requests if needed.
  
  If you prefer to use two workers (for example, to utilize two CPU cores), you can do `--workers 2`. But avoid spawning many worker processes unnecessarily; each will have its own connection to Meilisearch and memory overhead. One or two should suffice as required.
- **Connection to Meilisearch:** The Python client uses HTTP under the hood. Ensure you create the client object once (e.g., at startup) and reuse it, rather than creating a new client on each request. Reusing the client allows persistent HTTP connection (keep-alive) usage, avoiding TCP handshake overhead each time.
- **Query efficiency:** Meilisearch is optimized for speed, but to keep response times low:
  - Limit the number of results returned per query to a reasonable number (e.g., top 10 or 20 hits). This reduces the amount of data to transfer and process in Python. The API can support pagination if needed (pass `limit` and `offset` in search).
  - Use Meilisearch’s search parameters to your advantage. For example, if definitions are very long and you don’t want to send the entire text, you can request only a snippet. Meilisearch supports an `attributesToRetrieve` parameter; you could choose to retrieve only the headword and maybe a shortened excerpt. However, for an AI-friendly output, it might be better to return the full definition so the AI has complete info. Weigh the trade-offs based on typical definition length.
  - Ensure the index is loaded in memory. The first query to Meilisearch might be slightly slower if it needs to load data from disk, but subsequent queries stay in memory. For a production service, you might “warm up” the service by performing a sample query at startup (e.g., search for a common word) to prime the cache.
- **Avoiding Python bottlenecks:** In the request handling code, do minimal processing. Essentially, accept the query, pass it to Meilisearch, then format the response. The heavy lifting (searching, ranking) is done in Meilisearch’s optimized engine. Python should not iterate over large datasets in the query path. At most, it will loop over the small list of hits returned (e.g., 10 results) to format or add extra fields – that’s negligible.
- **Threading vs Async:** We will likely write the endpoint function to call Meilisearch synchronously (using the client library). If the client library is not async, FastAPI will offload that to a thread behind the scenes (because it knows standard functions run in a threadpool). This is fine for our low thread count scenario. Alternatively, you can use an async HTTP library like **httpx** to call Meilisearch’s REST API directly in an `async def` function, avoiding threads entirely. For simplicity, using the official client (which internally might use the `requests` library) is acceptable; just keep in mind it might block a thread during the HTTP call (again, one thread can handle one request at a time, which is okay with our single-worker assumption).
- **Meilisearch performance tuning:** Meilisearch itself can be tuned with configuration options if needed:
  - It uses memory-mapped files (LMDB). Ensure the machine has enough RAM for the index (for 100MB text, index might be a couple hundred MB footprint – well within modern systems).
  - If you observe any slowdown, check if CPU is saturated (unlikely unless complex queries) or if disk I/O is happening (shouldn’t after initial load). Usually, no special tuning is required for Meilisearch for this data size and query rate.
  - Typo tolerance and complex query features (like facet filtering, etc.) can slightly add overhead. We are mostly doing straightforward full-text queries, which are fast.
  
By following these practices, the **end-to-end search request** (from HTTP request -> FastAPI -> Meilisearch -> FastAPI -> HTTP response) should typically complete in a few tens of milliseconds, leaving plenty of headroom under 500ms. Even under load or on modest hardware, this stack is efficient. For example, FastAPI’s asynchronous nature “**allows multiple requests concurrently with a single worker, leading to better resource utilization** ([Flask vs FastAPI: An In-Depth Framework Comparison | Better Stack Community](https://betterstack.com/community/guides/scaling-python/flask-vs-fastapi/#:~:text=FastAPI%20can%20handle%20multiple%20requests,leading%20to%20better%20resource%20utilization)),” which means even if one request is waiting on Meilisearch I/O, another can be processed in the meantime.

## 5. Ranking & Relevance Tuning

Out-of-the-box, Meilisearch’s relevance sorting should be suitable: it will rank exact matches higher and incorporate typo count and term frequency seamlessly. Still, we should ensure our search results make sense for dictionary use, and optionally provide a **confidence score** in the API results.

**Default ranking rules:** As mentioned, Meilisearch uses a sequence of rules to sort results ([Ranking Rules Setting API | Welcome to the Meilisearch specifications!](https://specs.meilisearch.dev/specifications/text/0123-ranking-rules-setting-api.html#:~:text=Built,Proximity%3B%20Attribute%3B%20Sort%3B%20Exactness)). A brief overview:
- **Words**: Prioritizes documents that have more of the query terms (or all query terms).
- **Typo**: Among those, ones with fewer typos (edit distance) rank higher.
- **Proximity**: If query has multiple terms, documents where those terms appear closer together rank higher.
- **Attribute**: If we defined field order in `searchableAttributes`, and a match is found in a higher-priority field (like the headword), that doc ranks higher than one where the match is only in a lower field (like the definition) ([How can a complete novice get started using this? I want to index & search HTML files. · meilisearch meilisearch · Discussion #1881 · GitHub](https://github.com/meilisearch/meilisearch/discussions/1881#:~:text=The%20advantage%20of%20this%20second,all%20depends%20on%20your%20real)).
- **Sort**: Not used unless we specify a custom sort predicate in the query.
- **Exactness**: If a document contains an exact match of the whole query vs just partial or fuzzy matches, it’s boosted.

These ensure that, for example, if the user searches “forest”, an entry with the headword “forest” will rank above an entry where the word “forest” only appears in an example sentence. Likewise, a perfectly spelled query will bring the exact match first, whereas a query with one letter off will still find the entry but maybe with slightly lower score if an exact match of the typo exists somewhere.

**Custom tuning:** We can adjust a few things:
- If we want headword matches to always outrank definition matches, ensure the `searchableAttributes` are in the order [term, definition], as set earlier. This leverages the **attribute ranking rule** to favor headword.
- If certain fields or criteria should influence rank (not likely in a dictionary scenario, but for example, if we had a frequency or importance score for entries), Meilisearch allows adding **custom ranking rules** based on numeric fields. We probably won’t need this.
- We might disable or adjust typo tolerance in some cases (e.g., if the dictionary contains many short words or acronyms where typos could cause odd matches, one can configure `minWordSizeForTypos` for 1 typo or 2 typos separately).
- If multi-language entries are in the same index, sometimes boosting might be needed to prefer one language over another if desired. But likely, we treat them equally.

**Relevance score or confidence:** The API should ideally return a relevance score with each result so that clients (or AI agents) know how good the match is. Meilisearch can provide a normalized **ranking score** if requested. In the search query, set `showRankingScore=true` to get a `_rankingScore` field for each hit ([Ranking Score | Welcome to the Meilisearch specifications!](https://specs.meilisearch.dev/specifications/text/0195-ranking-score.html#:~:text=A%20ranking%20score%20is%20a,true%20in%20the%20search%20query)). This score ranges from 0.0 to 1.0, where 1.0 means a perfect match and 0.0 means no match (documents with no match won’t be returned at all) ([Ranking Score | Welcome to the Meilisearch specifications!](https://specs.meilisearch.dev/specifications/text/0195-ranking-score.html#:~:text=The%20ranking%20score%20is%20contained,do%20not%20match%20the%20query)). The score is influenced by the ranking rules and gives a measure of confidence relative to the query.

We will use this feature to include a confidence score:
- In the Python client, this can be done by passing the search parameters. For example: 
  ```python
  results = index.search(query, {"showRankingScore": True})
  ```
  The returned JSON will have something like:
  ```json
  "hits": [
    {
      "id": "123",
      "term": "forest",
      "definition": "wooded area...",
      "_rankingScore": 0.98
    }, ...
  ]
  ```
  (The exact key might be `_rankingScore` or `rankingScore` depending on the version.) We can extract that and include it in our API’s result for each item as a confidence.

If for some reason we couldn’t get a numeric score, a simpler proxy is to use the rank (position) or the presence of typos as a confidence indicator. But since Meilisearch supports `showRankingScore`, we should use it. This **score is independent of other docs** and only depends on the document’s match with the query and index settings ([Ranking Score | Welcome to the Meilisearch specifications!](https://specs.meilisearch.dev/specifications/text/0195-ranking-score.html#:~:text=The%20ranking%20score%20is%20contained,do%20not%20match%20the%20query)), so it’s stable for our use.

**Testing relevance:** After setting up, test a few queries in each language:
- Exact match queries (should return that entry with score ~1.0).
- Slightly misspelled queries (should still find the entry, maybe score a bit lower).
- Multi-word queries (if your dictionary entries can be found by a phrase).
- Ensure that Russian and Ossetian queries retrieve appropriate entries (e.g., searching Осетия finds entries about Ossetia, etc.). If you notice any odd ranking (like a less relevant entry above a more relevant one), you may adjust the ranking rules or synonyms accordingly.

## 6. Designing the OpenAPI-Compliant API (FastAPI vs Flask, etc.)

For the API layer, **FastAPI** is recommended due to its performance and automatic OpenAPI documentation generation. FastAPI allows us to define endpoints and data models, and it will produce a **Swagger UI** and **ReDoc** documentation out-of-the-box ([Features - FastAPI](https://fastapi.tiangolo.com/features/#:~:text=Interactive%20API%20documentation%20and%20exploration,options%2C%202%20included%20by%20default)). This means any consumer (including AI agents) can easily inspect the API structure and understand request/response formats.

**Why FastAPI over Flask:**
- **Built-in OpenAPI support:** FastAPI is built on OpenAPI standards; simply defining your endpoint functions and Pydantic models will generate a schema. Swagger UI is served at `/docs` by default, and a machine-readable JSON schema is at `/openapi.json` ([Features - FastAPI](https://fastapi.tiangolo.com/features/#:~:text=Interactive%20API%20documentation%20and%20exploration,options%2C%202%20included%20by%20default)). This is crucial for AI usability – an AI agent can read the OpenAPI spec to understand how to call the API.
- **Performance:** FastAPI is asynchronous and built for speed. It’s one of the highest-performing Python frameworks, outperforming Flask significantly under load ([Flask vs FastAPI: An In-Depth Framework Comparison | Better Stack Community](https://betterstack.com/community/guides/scaling-python/flask-vs-fastapi/#:~:text=FastAPI%20can%20handle%20multiple%20requests,leading%20to%20better%20resource%20utilization)) ([Flask vs FastAPI: An In-Depth Framework Comparison | Better Stack Community](https://betterstack.com/community/guides/scaling-python/flask-vs-fastapi/#:~:text=Real,increases%2C%20particularly%20with%20I%2FO%20operations)). Given our requirement for minimal threads, FastAPI shines (concurrent async handling in a single thread).
- **Developer ergonomics:** Using Python type hints and Pydantic, we can define request and response data models that are validated and documented. This reduces boilerplate compared to Flask (where you’d manually parse `request.args` or `request.json` and write validation).
- **Example:** In FastAPI we can do:
  ```python
  from fastapi import FastAPI, Query
  from pydantic import BaseModel
  app = FastAPI(title="Dictionary Search API", version="1.0")

  class SearchResponse(BaseModel):
      query: str
      results: list[dict]  # we will refine this to a list of result model
      processing_time_ms: int
      total_hits: int

  @app.get("/search", response_model=SearchResponse)
  async def search(q: str = Query(..., description="The search query (word or phrase)")):
      # ... perform search
      return {...}  # must match SearchResponse structure
  ```
  With this, FastAPI will automatically document the `/search` endpoint, the `q` parameter, and the shape of the response.

**Defining API endpoints:**
- We will create a **`GET /search`** endpoint as the main entry point. Query parameters can include:
  - `q` (string): the search query (required).
  - (Optional) `language` or `lang` if you wanted to influence search by language. However, if the index is combined and supports all languages, this may not be needed. Alternatively, we could use it if we had separate indexes per language, but we assume one index.
  - (Optional) paging parameters like `page` or `offset` & `limit`. Meilisearch can handle `offset` and `limit`; we might expose something like `limit` in the API (with a sane default like 10).
- Example OpenAPI path for search in FastAPI will show a parameter `q` in the query. FastAPI’s docs UI will allow testing it easily.

**Response design:** The response should be **structured, easy-to-read, and AI-friendly**:
- Use clear JSON keys. Avoid unnecessary nesting. A flat or moderately nested structure is easier for an LLM to parse.
- Include the original query in the response for clarity (`"query": "forest"` for example).
- Provide an array of results under a key like `"results"` or `"hits"`. Each result can be an object containing:
  - The dictionary **entry text** – possibly split into `"term"` and `"definition"` fields, or combined if that’s more convenient. For AI usage, having the headword separate might be useful (the AI could identify the headword vs its explanation).
  - A **score/confidence** field (e.g., `"score": 0.95`). We might scale Meilisearch’s 0.0–1.0 score to a percentage or leave as float.
  - Possibly an `"id"` if the client might use it for follow-up (though not strictly needed if all relevant info is present).
- Additional metadata: It’s good to include `"total_hits"` (how many results matched) and `"processing_time_ms"` (how long the search took), which Meilisearch returns in its response. This helps the client/AI gauge the result set and speed.
- Example response JSON:
  ```json
  {
    "query": "forest",
    "total_hits": 3,
    "processing_time_ms": 5,
    "results": [
      {
        "term": "Forest",
        "definition": "A large area covered chiefly with trees and undergrowth.",
        "score": 0.98
      },
      {
        "term": "Forestry",
        "definition": "The science or practice of planting, managing, and caring for forests.",
        "score": 0.72
      },
      {
        "term": "Forestall",
        "definition": "To prevent or obstruct by taking action ahead of time.",
        "score": 0.68
      }
    ]
  }
  ```
  This structure is easy for both humans and AI to read. Each result’s relevance is clear from the score. The AI can pick the top result or decide if multiple are relevant.

**AI-friendly formatting:** Some tips to make it especially AI-usable:
- Keep definitions text clean – no HTML tags or extraneous formatting. Just plain sentences. If the dictionary content had formatting (italics, etc.), consider either removing them or using simple Markdown if necessary for clarity (but plain text is safest for AI parsing).
- Use consistent field names and types (FastAPI/Pydantic helps enforce this). The OpenAPI spec will show these field names and types, so an AI agent could automatically interpret that `"term"` is a string for the headword, etc.
- Avoid including things like raw HTML or overly verbose nested objects that might confuse a language model. Our structure above is straightforward.
- Provide example responses in the OpenAPI docs (FastAPI allows you to include example in the response model or docstring). This can illustrate to users (and possibly AI) what to expect.

**Error handling:** Also define how errors are returned (e.g., if `q` is missing, FastAPI will auto-handle that with a 422 validation error). You might want to catch exceptions (like if Meilisearch is not reachable) and return a clean JSON error. Possibly define a model for errors:
  ```json
  { "error": "Unable to connect to search engine" }
  ```
  with appropriate status codes (500, etc.). FastAPI can include these in the OpenAPI schema as well.

**CORS and local usage:** If this is purely local (accessed by local apps or via an AI agent on the same machine), CORS might not be an issue. If a web UI or external agent (like a browser or another domain) needs to request it, enable CORS in FastAPI:
  ```python
  from fastapi.middleware.cors import CORSMiddleware
  app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])
  ```
  This allows cross-origin requests (adjust origins in production for security). This is only needed if calling the API from a web page; an AI running locally can call the API directly without CORS.

**API Framework alternatives:** While we champion FastAPI, for completeness:
- **Flask:** Flask could be used but would require manual documentation (using something like flasgger or writing an OpenAPI spec by hand). It’s also synchronous by nature. It’s simple, but given our requirements (especially OpenAPI spec generation and performance), Flask is less suited.
- **Falcon or Starlette:** Lower-level frameworks could offer performance, but again lack the automatic documentation and nice features FastAPI provides.
- **OpenAPI generation tools:** FastAPI covers this. If we were to use Flask, we’d need to generate a Swagger JSON. It’s doable but more work.
  
Thus, we’ll proceed with FastAPI for implementation.

## 7. Implementation Roadmap

Putting it all together, here’s a step-by-step plan to implement the server:

### A. Setup and Installation
1. **Install Meilisearch** – either via Docker or by downloading the binary from the Meilisearch website. Ensure it’s running and accessible (e.g., on localhost:7700). Note the master key if security is enabled.
2. **Create a Python environment** – use Python 3.9+ (FastAPI and Pydantic benefit from newer Python for type hints). Install required libraries:
   - FastAPI (for the API) – `pip install fastapi uvicorn`
   - Meilisearch Python client – `pip install meilisearch`
   - BeautifulSoup and lxml (for parsing HTML) – `pip install beautifulsoup4 lxml`
   - (Optional) uvloop for faster event loop on Linux – `pip install uvloop` (Uvicorn will use it if available).
   - (Optional) pymorphy2 or similar if doing advanced Russian stemming/synonyms – not required unless you choose to implement that.
3. **Project structure:** organize your code. For example:
   - `app.py` – where you initialize FastAPI and define endpoints.
   - `search_engine.py` – code to initialize Meilisearch client, load/index data (could be run at startup or separately).
   - `models.py` – Pydantic models for request/response (or define in app.py for simplicity).
   - `data/Dicts/` – your HTML files (if needed in code; or you might load them once and build the index).

### B. Data Preprocessing & Indexing
1. **Read and parse HTML files:** Use Python to iterate through the "Dicts" directory. For each file:
   - Open it (ensure correct encoding, likely UTF-8).
   - Parse content with BeautifulSoup(lxml).
   - Find entry elements and extract `term` and `definition`.
   - Append to a list of documents.
   - (Memory optimization: index in batches and clear list as discussed).
2. **Initialize Meilisearch index:** Connect to Meilisearch with the client. Create the index (if not exist) with the chosen primary key.
3. **Configure index settings:** Set `searchableAttributes = ["term", "definition"]` (or appropriate field names). Also set any `synonyms` or `stopWords` needed for multilingual support.
4. **Add documents:** Push the documents to Meilisearch, batching as needed. Use `showRankingScore` in queries (not at indexing time) – so no config needed for that now.
5. **Verify indexing success:** You can log the number of documents indexed, or use `index.get_documents(limit=1)` to see one document. Also, Meilisearch’s console logs or `/indexes/dictionary` info can confirm document count.

It’s often wise to perform this indexing step as a **one-time setup** or on startup of the server. If the data doesn’t change often, you can index once and reuse the Meilisearch data files on each run (Meilisearch will persist data on disk in its `data.ms` directory). In production, you might separate the indexing phase from the API server startup to avoid re-indexing each time. For example, run a script `index_data.py` once to load the data, then launch the API which will simply connect to the already-built index. If the dictionary content updates, you would run an indexing update again.

### C. API Development
1. **Initialize FastAPI app:** in `app.py`:
   ```python
   from fastapi import FastAPI, Query
   from pydantic import BaseModel
   import meilisearch

   app = FastAPI(title="Dictionary Search API", version="1.0", description="Full-text search API for a multilingual dictionary (English, Russian, Ossetian).")

   # Meilisearch client and index
   MEILI_URL = "http://127.0.0.1:7700"
   MEILI_KEY = "masterKey"  # replace with actual key or use env var
   meili_client = meilisearch.Client(MEILI_URL, MEILI_KEY)
   index = meili_client.index("dictionary")
   ```
   It’s good to instantiate the client at module level so it’s created once. (In a larger app, you might use FastAPI’s startup event to do this).
2. **Define response models:** Use Pydantic to define the shape of the response. E.g.:
   ```python
   class SearchResult(BaseModel):
       term: str
       definition: str
       score: float

   class SearchResponse(BaseModel):
       query: str
       total_hits: int
       processing_time_ms: int
       results: list[SearchResult]
   ```
   This ensures the output is validated and documented. Each SearchResult will contain the fields we want to expose. We exclude internal things like the Meilisearch `_matchesInfo` or internal IDs from the API.
3. **Implement the search endpoint:**
   ```python
   @app.get("/search", response_model=SearchResponse)
   async def search(q: str = Query(..., min_length=1, description="Search query (term or phrase, in English, Russian, or Ossetian)"),
                   limit: int = Query(10, ge=1, le=50, description="Number of results to return (max 50)")):
       # Perform search using Meilisearch
       try:
           result = index.search(q, {"showRankingScore": True, "limit": limit})
       except Exception as e:
           # If Meilisearch is not reachable or other error
           raise HTTPException(status_code=500, detail=str(e))
       hits = result.get("hits", [])
       # Build results list
       results_list = []
       for hit in hits:
           results_list.append({
               "term": hit.get("term", ""),
               "definition": hit.get("definition", ""),
               "score": hit.get("_rankingScore", 0.0)
           })
       response = {
           "query": q,
           "total_hits": result.get("nbHits", len(hits)),
           "processing_time_ms": result.get("processingTimeMs", 0),
           "results": results_list
       }
       return response
   ```
   A few notes on the above:
   - We declare `q` as a required query parameter. FastAPI will enforce `min_length=1` to prevent empty queries.
   - We include a `limit` param to control page size (default 10, max 50 for example). We pass that to Meilisearch’s search call.
   - `index.search` returns a dict with keys like `hits`, `nbHits`, `processingTimeMs`, etc. We extract those.
   - We map each hit to our `SearchResult` structure. We use `.get` to avoid KeyErrors just in case. We default `score` to 0.0 if `_rankingScore` missing (which shouldn’t be if we set the flag).
   - We handle exceptions by returning a HTTP 500 with error detail. In production, you might not want to expose raw error (could just say “Internal Server Error”), but this is fine for local service.
   - The `response_model=SearchResponse` tells FastAPI to validate the returned structure matches SearchResponse. It also will trim any extra fields not defined (e.g., if we accidentally left the internal `_rankingScore` in the dict, Pydantic would drop it since SearchResult doesn’t have that field).

4. **Documentation & Testing:** Start the server (`uvicorn app:app --reload`) and open the interactive docs at `http://localhost:8000/docs`. You should see the `GET /search` endpoint, with parameters documented. Try it out with various queries to ensure it returns expected data. This interactive Swagger UI is very helpful for debugging.
   - The OpenAPI JSON at `/openapi.json` will include the schemas for SearchResponse and SearchResult, which is useful if integrating with tools or for an AI to read.
   - If you want to make the docs even more descriptive, you can add more info in the FastAPI `description` and `summary` for the endpoint, and in docstrings.
   - Example: 
     ```python
     @app.get("/search", response_model=SearchResponse, summary="Search the dictionary", description="Full-text search in the multilingual dictionary. Supports typo-tolerant search in English, Russian, and Ossetian.")
     ```
     This gives a human-friendly explanation in the docs UI.

5. **AI Usability Consideration:** The responses are already JSON, which is great for AI consumption. If you plan to have an LLM agent directly ingest these, ensure it gets the raw JSON (not an HTML-rendered view). Since this is a local service, an LLM could call it via tools or a function call interface. The clear key names (“term”, “definition”, “score”) make it easy for the LLM to pick out the definition or decide which result is best. No further changes needed specifically for AI.

### D. Additional Optimizations and Considerations

1. **Logging and Monitoring:** For a production service, set up logging (FastAPI/Uvicorn logs requests by default). Monitor the response times and any errors. Meilisearch also logs search timings; if you see any queries taking long, investigate (e.g., maybe a very large query or a pathological case).
2. **Security:** If the service is running locally for personal/AI use, security is less a concern. But if exposed elsewhere, consider:
   - Using API keys or OAuth (FastAPI can integrate authentication easily) to protect the endpoint.
   - Rate limiting if needed (to prevent abuse; unlikely needed locally).
   - Disabling or protecting the docs in production (you can disable Swagger UI or make it require login if necessary).
3. **Threading in Meilisearch:** Meilisearch itself will utilize multiple threads for search internally. The Python server as we set is mostly single-threaded async. If you need to handle CPU-bound tasks (not likely here), you’d offload to a thread pool or background task. Searching is I/O-bound (waiting for Meilisearch to return over HTTP), so our approach is fine.
4. **Testing edge cases:** Search queries that contain multiple words, punctuation, etc. Meilisearch will ignore some punctuation by default. If a query is just a typo away from two different words, see how Meilisearch ranks them (the one with fewer edits should come first).
5. **Preprocessing improvements:** If dictionary text contains HTML entities or residual tags (like `&nbsp;` or `<i>` tags around examples), consider cleaning those out. You can use BeautifulSoup’s `.stripped_strings` or manually replace common entities. This ensures the definitions output is clean text.
6. **Scaling up:** If in the future the dataset grows (say more dictionaries or millions of entries), this architecture still holds. Meilisearch can handle millions of documents (with more RAM). FastAPI can scale by increasing workers or deploying behind a load balancer. For local use, this likely isn’t needed.
7. **Alternate search backends:** For completeness, there are other search engines like ElasticSearch or Typesense. We chose Meilisearch for simplicity and speed. Typesense is another typo-tolerant engine, Elastic can do advanced language analysis but is heavier. Meilisearch hits a sweet spot for ease-of-use vs performance, which is why we stick with it unless requirements change.
8. **Content updates:** If the dictionary content might update, plan how to handle re-indexing. Meilisearch supports updating documents by primary key. You could create an admin endpoint to trigger re-indexing or directly update specific entries. This is out of scope for now (assuming static data), but keep in mind maintainability.

## 8. Conclusion

By following this guide, you can implement a robust local search service that meets all the requirements:
- **Meilisearch** provides fast, typo-tolerant full-text search with multilingual support (English, Russian, Ossetian) ([How to add Russian language suport? · Issue #612 · meilisearch/meilisearch · GitHub](https://github.com/meilisearch/MeiliSearch/issues/612#:~:text=Kerollmops%20%20%20commented%20,67)).
- **Data ingestion** is handled by parsing HTML dictionary files with BeautifulSoup (using the fast lxml parser for efficiency) ([Making beautifulsoup Parsing 10 times faster - The HFT Guy](https://thehftguy.com/2020/07/28/making-beautifulsoup-parsing-10-times-faster/#:~:text=The%20internet%20is%20unanimous%2C%20one,should%20be%20much%20much%20faster)), and indexing each entry as a document in Meilisearch. We split entries for optimal search granularity as recommended in Meilisearch discussions (extracting structured fields for better relevancy) ([How can a complete novice get started using this? I want to index & search HTML files. · meilisearch meilisearch · Discussion #1881 · GitHub](https://github.com/meilisearch/meilisearch/discussions/1881#:~:text=2,work%20on%20the%20document%20preparation)) ([How can a complete novice get started using this? I want to index & search HTML files. · meilisearch meilisearch · Discussion #1881 · GitHub](https://github.com/meilisearch/meilisearch/discussions/1881#:~:text=The%20advantage%20of%20this%20second,all%20depends%20on%20your%20real)).
- **FastAPI** is used to create an OpenAPI-compliant REST API. It automatically generates documentation and allows high performance with minimal threads ([Flask vs FastAPI: An In-Depth Framework Comparison | Better Stack Community](https://betterstack.com/community/guides/scaling-python/flask-vs-fastapi/#:~:text=FastAPI%20can%20handle%20multiple%20requests,leading%20to%20better%20resource%20utilization)). The API outputs well-structured JSON that is easy for AI agents to parse.
- **Ranking** is tuned using Meilisearch’s default rules and we expose a relevance score for each result, which helps consumers understand the confidence of matches. The use of `showRankingScore` yields a 0.0–1.0 score denoting match quality ([Ranking Score | Welcome to the Meilisearch specifications!](https://specs.meilisearch.dev/specifications/text/0195-ranking-score.html#:~:text=The%20ranking%20score%20is%20contained,do%20not%20match%20the%20query)).
- **Performance** is optimized by using asynchronous handling, efficient data structures, and keeping the workload in the search engine (which is written in optimized Rust). Sub-500ms response is achievable even on modest hardware for our data size.

By adhering to these steps and best practices, an LLM-based coder (or any developer) can implement the project end-to-end without needing additional clarification. The combination of Meilisearch and FastAPI provides a powerful yet developer-friendly stack to accomplish typo-tolerant multilingual search, and the OpenAPI documentation ensures the service is easily consumable by both humans and AI tools.
