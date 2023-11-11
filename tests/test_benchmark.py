import unittest

from hashedixsearch.search import HashedIXSearch


class TestBenchmark(unittest.TestCase):
    documents = [
        "red bell pepper diced",
        "onions",
        "mayonnaise",
        "whole onion",
        "five onions, diced",
        "egg & bacon",
        "one carrot",
        "Wine",
        "Place in Dutch Oven, and leave for one hour",
        "daal daal daal",
        "one two three",
        "mushrooms",
        "tofu",
        "can of baked beans",
        "sliced red bell pepper as filling",
        "put the skewer in the frying pan",
        "put the kebab skewers in the pan",
        "60 ml crème fraîche",
        "preheat the oven to 300 degrees",
        "Step one, oven.  Phase two: pan.",
        "food mill.",
        "medium onion",
        "garlic",
        "place in the bread maker",
        "clove",
        "garlic",
        "place the towel onto the place mat",
        "empty term example",
    ] * 100

    stopwords = [
        "diced",
        "whole",
    ]

    queries = [
        "tofu",
        "egg",
        "garlic",
        "mushroom",
        "beans",
        "onion",
        "carrot",
        "daal",
        "bread",
        "nonexistent",
        "crème",
        "kebab",
        "bell pepper",
    ] * 100

    def test_benchmark(self):
        index = HashedIXSearch(stopwords=self.stopwords)
        for doc_id, doc in enumerate(self.documents):
            index.add(doc_id, doc)

        for query_id, query in enumerate(self.queries):
            index.query(query, query_limit=5)
            hits = index.query(query, query_limit=-1)
            self.assertTrue(hits or query in ["mushroom", "nonexistent"], query)

            if not hits:
                continue

            index.highlight(doc=self.documents[query_id], terms=hits[0]["terms"])
