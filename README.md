# hashedixsearch

`hashedixsearch` is a lightweight in-process search engine for Python, with support for stemming, synonyms, custom token analyzers, and query match highlighting.

## Usage

```python
from hashedixsearch import HashedIXSearch

index = HashedIXSearch(synonyms={'search': 'find'})
index.add(
    doc_id=1,
    doc='find the needle in the haystack'
)

results = index.query_batch(['search'])
for query, hits in results:
    print(f'{query}: {hits}')
```

## Tests

To run the `hashedixsearch` test suite:

```bash
$ python -m unittest
```

This library uses [hashedindex](https://github.com/MichaelAquilina/hashedindex) for tokenization and indexing.
