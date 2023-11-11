import unittest

from unidecode import unidecode

from hashedixsearch.search import HashedIXSearch


class TestSearch(unittest.TestCase):
    class NaivePluralStemmer(object):
        @staticmethod
        def stem(word):
            return word.rstrip("s")

    class UnidecodeStemmer(object):
        @staticmethod
        def stem(word):
            return unidecode(word)

    def test_tokenize_stopwords(self):
        doc = "red bell pepper diced"
        stopwords = ["diced"]

        index = HashedIXSearch(stopwords=stopwords)
        tokens = list(index.tokenize(doc=doc))

        self.assertEqual(tokens[0], ("red", "bell", "pepper"))

    def test_token_stemming(self):
        doc = "onions"

        stemmer = self.NaivePluralStemmer()
        index = HashedIXSearch()
        tokens = list(index.tokenize(doc=doc, stemmer=stemmer))

        self.assertEqual(tokens[0], ("onion",))

    def test_query(self):
        doc = "mayonnaise"

        index = HashedIXSearch()
        index.add(0, doc)
        hits = index.query(doc)

        self.assertTrue(list(hits))

    def test_batch_query(self):
        docs = ["tomato", "onion"]

        index = HashedIXSearch()
        for doc in docs:
            index.add(0, doc)

        results = []
        for query in docs:
            hits = index.query(doc)
            results.append(hits)

        self.assertEqual(len(results), 2)
        self.assertTrue(all([hits for hits in results]))

    def test_exact_match(self):
        doc = "whole onion"
        stopwords = ["whole"]
        term = ("onion",)

        index = HashedIXSearch(stopwords=stopwords)
        index.add(0, doc)

        self.assertEqual(index.query_exact(term), 0)

    def test_exact_match_duplicate(self):
        doc = "whole onion"
        stopwords = ["whole"]
        term = ("onion",)

        index = HashedIXSearch(stopwords=stopwords)
        index.add(0, doc)
        index.add(0, doc)

        self.assertEqual(index.query_exact(term), 0)

    def test_highlighting(self):
        doc = "five onions, diced"
        term = ("onion",)

        stemmer = self.NaivePluralStemmer()
        index = HashedIXSearch(stemmer=stemmer)
        markup = index.highlight(doc, [term])

        self.assertEqual(markup, "five <mark>onions</mark>, diced")

    def test_highlighting_escaping(self):
        doc = "egg & bacon"
        terms = [("egg",), ("bacon",)]

        stemmer = self.NaivePluralStemmer()
        index = HashedIXSearch(stemmer=stemmer)
        markup = index.highlight(doc, terms)

        self.assertEqual(markup, "<mark>egg</mark> &amp; <mark>bacon</mark>")

    def test_highlighting_unstemmed(self):
        doc = "one carrot"
        term = ("carrot",)

        index = HashedIXSearch()
        markup = index.highlight(doc, [term])

        self.assertEqual(markup, "one <mark>carrot</mark>")

    def test_highlighting_case_insensitive_term(self):
        doc = "Wine"
        term = ("wine",)

        index = HashedIXSearch()
        markup = index.highlight(doc, [term], case_sensitive=False)

        self.assertEqual(markup, "<mark>Wine</mark>")

    def test_highlighting_case_insensitive_phrase(self):
        doc = "Place in Dutch Oven, and leave for one hour"
        term = ("dutch", "oven")
        expected = "Place in <mark>Dutch Oven</mark>, and leave for one hour"

        index = HashedIXSearch()
        markup = index.highlight(doc, [term], case_sensitive=False)

        self.assertEqual(markup, expected)

    def test_highlighting_partial_match_ignored(self):
        doc = "Place in Dutch oven, and leave for one hour"
        term = ("dutch", "oven")

        index = HashedIXSearch()
        markup = index.highlight(doc, [term])

        self.assertEqual(markup, "Place in Dutch oven, and leave for one hour")

    def test_highlighting_repeat_match(self):
        doc = "daal daal daal"
        term = ("daal",)
        expected = "<mark>daal</mark> <mark>daal</mark> <mark>daal</mark>"

        index = HashedIXSearch()
        markup = index.highlight(doc, [term])

        self.assertEqual(markup, expected)

    def test_highlighting_match_limit(self):
        doc = "one two three"
        terms = [("one",), ("two",), ("three",)]
        expected = "<mark>one</mark> <mark>two</mark> three"

        index = HashedIXSearch()
        markup = index.highlight(doc, terms, limit=2)

        self.assertEqual(markup, expected)

    def test_highlighting_empty_terms(self):
        doc = "mushrooms"

        index = HashedIXSearch()
        markup = index.highlight(doc, [])

        self.assertEqual(markup, doc)

    def test_highlighting_term_larger_than_query(self):
        doc = "tofu"
        term = ("pack", "tofu")

        stemmer = self.NaivePluralStemmer()
        index = HashedIXSearch(stemmer=stemmer)
        markup = index.highlight(doc, [term])

        self.assertEqual(markup, "tofu")

    def test_phrase_term_highlighting(self):
        doc = "can of baked beans"
        term = ("baked", "bean")

        stemmer = self.NaivePluralStemmer()
        index = HashedIXSearch(stemmer=stemmer)
        markup = index.highlight(doc, [term])

        self.assertEqual(markup, "can of <mark>baked beans</mark>")

    def test_trigram_phrase_term_highlighting(self):
        doc = "sliced red bell pepper as filling"
        term = ("red", "bell", "pepper")

        index = HashedIXSearch()
        markup = index.highlight(doc, [term])

        self.assertEqual(markup, "sliced <mark>red bell pepper</mark> as filling")

    def test_phrase_multi_term_highlighting(self):
        doc = "put the skewer in the frying pan"
        terms = [
            ("skewer",),
            ("frying", "pan"),
        ]
        expected = "put the <mark>skewer</mark> in the <mark>frying pan</mark>"

        stemmer = self.NaivePluralStemmer()
        index = HashedIXSearch(stemmer=stemmer)
        markup = index.highlight(doc, terms)

        self.assertEqual(markup, expected)

    def test_phrase_multi_term_highlighting_extra(self):
        doc = "put the kebab skewers in the pan"
        terms = [
            ("kebab", "skewer"),
            ("pan",),
        ]
        expected = "put the <mark>kebab skewers</mark> in the <mark>pan</mark>"

        stemmer = self.NaivePluralStemmer()
        index = HashedIXSearch(stemmer=stemmer)
        markup = index.highlight(doc, terms)

        self.assertEqual(markup, expected)

    def test_highlighting_non_ascii(self):
        doc = "60 ml crème fraîche"
        term = ("creme", "fraiche")

        stemmer = self.UnidecodeStemmer()
        index = HashedIXSearch(stemmer=stemmer)
        markup = index.highlight(doc, [term])

        self.assertEqual(markup, "60 ml <mark>crème fraîche</mark>")

    def test_retain_numbers(self):
        doc = "preheat the oven to 300 degrees"
        terms = [("oven",), ("300",)]
        expected = "preheat the <mark>oven</mark> to <mark>300</mark> degrees"

        index = HashedIXSearch()
        markup = index.highlight(doc, terms)

        self.assertEqual(markup, expected)

    def test_retained_style(self):
        doc = "Step one, oven.  Phase two: pan."
        terms = [("oven",), ("pan",)]
        expected = "Step one, <mark>oven</mark>.  Phase two: <mark>pan</mark>."

        stemmer = self.NaivePluralStemmer()
        index = HashedIXSearch(stemmer=stemmer)
        markup = index.highlight(doc, terms)

        self.assertEqual(markup, expected)

    def test_ambiguous_prefix(self):
        doc = "food mill."
        terms = [("food", "processor"), ("food", "mill")]

        stemmer = self.NaivePluralStemmer()
        index = HashedIXSearch(stemmer=stemmer)
        markup = index.highlight(doc, terms)

        self.assertEqual(markup, "<mark>food mill</mark>.")

    def test_partial_suffix(self):
        doc = "medium onion"
        terms = [("onion", "gravy")]

        stemmer = self.NaivePluralStemmer()
        index = HashedIXSearch(stemmer=stemmer)
        markup = index.highlight(doc, terms)

        self.assertEqual(markup, "medium onion")

    def test_term_attributes(self):
        doc = "garlic"
        term = ("garlic",)

        terms = [term]
        term_attributes = {term: {"id": "example"}}

        stemmer = self.NaivePluralStemmer()
        index = HashedIXSearch(stemmer=stemmer)
        markup = index.highlight(doc, terms, term_attributes=term_attributes)

        self.assertEqual(markup, '<mark id="example">garlic</mark>')

    def test_term_attributes_phrase_query(self):
        doc = "place in the bread maker"
        term = ("bread", "maker")

        terms = [term]
        term_attributes = {term: {"id": "example"}}

        index = HashedIXSearch()
        markup = index.highlight(doc, terms, term_attributes=term_attributes)

        self.assertEqual(markup, 'place in the <mark id="example">bread maker</mark>')

    def test_hit_scoring(self):
        precise_match = "garlic"
        imprecise_match = "clove garlic"

        index = HashedIXSearch()
        index.add(0, precise_match)
        index.add(1, imprecise_match)

        hits = index.query("garlic")

        self.assertEqual(len(hits), 2)
        self.assertEqual(hits[0]["doc_id"], 0)

    def test_term_frequency_tiebreaker(self):
        infrequent_doc = "clove"
        frequent_doc = "garlic"

        index = HashedIXSearch()
        index.add(0, infrequent_doc)
        index.add(1, frequent_doc, count=5)

        for query in ("garlic clove", "clove garlic"):
            hits = index.query(query, query_limit=-1)

            self.assertEqual(len(hits), 2)
            self.assertEqual(hits[0]["doc_id"], 1)

    def test_multiterm_match_preference(self):
        uniterm_doc = "salsa"
        multiterm_doc = "salsa verde"

        index = HashedIXSearch()
        index.add(0, uniterm_doc, count=5)
        index.add(1, multiterm_doc)

        hits = index.query("salsa verde (green salsa)", query_limit=-1)

        self.assertEqual(len(hits), 2)
        self.assertEqual(hits[0]["doc_id"], 1)

    def test_partial_phrase_reoccurrence(self):
        doc = "place the towel onto the place mat"
        term = ("place", "mat")
        expected = "place the towel onto the <mark>place mat</mark>"

        index = HashedIXSearch()
        markup = index.highlight(doc, [term])

        self.assertEqual(markup, expected)

    def test_empty_term_handled(self):
        doc = "empty term example"
        term = tuple()
        expected = "empty term example"

        index = HashedIXSearch()
        markup = index.highlight(doc, [term])

        self.assertEqual(markup, expected)
