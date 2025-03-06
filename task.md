# OpenAPI server to serve html files with OCRd dictionaries

Write an OpenAPI server that will search text in a dictionary that is in a scanned HTML format, and then give out enough context for an OpenAPI user to use that. The server should be in Python, an openAPI user will be an AI agent, the queries might not be in English, but also in Russian and Ossetian(!), so it is important to be typo-resistant.

  * I refer Meilisearch as a search engine
  * full text search is a must
  * typo-tolerance is a must
  * the data size if 50-100mb of text
  * there's no need to further clean HTML, it has already been cleaned with LLMs
  * there's no need to try to extract entries of dictionaries: they are vastly different, and that will be too hard, just reply with enough context
  * you may index/preprocess data otherwise
  * preferrably, it should support stemming/lingvistic features that are possible for russian/ossetian
  * it will be a local service, so no need in highload overcomplications, all we need is to be able to reply in under half a second in one or two threads

The data in conclusion should be enough for an LLM-coder to make this project fully done.


## Additional considerations
I use uv, so run "uv pip install..." to install packages.
The dicts themselves are in folder Dicts/
