# hashedixsearch

`hashedixsearch` is a lightweight in-process search engine for Python, with support for stemming, custom token analyzers, and query match highlighting.

## Usage

```python
from hashedixsearch import HashedIXSearch

doc = 'find the needle in the haystack'

index = HashedIXSearch()
index.add(doc_id=1, doc=doc)

results = index.query_batch(['find'])
for query, hits in results:
    for hit in hits:
        # <mark>find</mark> the needle in the haystack
        markup = index.highlight(doc=doc, terms=hit['terms'])
```

This library uses [hashedindex](https://github.com/MichaelAquilina/hashedindex.git/) for tokenization and indexing.
