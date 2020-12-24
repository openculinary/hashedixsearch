from unidecode import unidecode

from hashedixsearch.search import HashedIXSearch, NullStemmer


class NaivePluralStemmer(NullStemmer):
    @staticmethod
    def stem(word):
        return word.rstrip("s")


class UnidecodeStemmer(NullStemmer):
    @staticmethod
    def stem(word):
        return unidecode(word)


def test_tokenize_stopwords():
    doc = "red bell pepper diced"
    stopwords = ["diced"]

    index = HashedIXSearch(stopwords=stopwords)
    tokens = list(index.tokenize(doc=doc))

    assert tokens[0] == ("red", "bell", "pepper")


def test_token_stemming():
    doc = "onions"

    index = HashedIXSearch()
    tokens = list(index.tokenize(doc=doc, stemmer=NaivePluralStemmer))

    assert tokens[0] == ("onion",)


def test_document_retrieval():
    doc = "mayonnaise"

    index = HashedIXSearch()
    index.add(0, doc)
    hits = index.query(doc)

    assert list(hits)


def test_analysis_consistency():
    doc = "soymilk"
    synonym = "soy milk"

    index = HashedIXSearch()
    index.add(0, "soymilk", synonyms={doc: synonym})
    hits = index.query("soy milk", synonyms={doc: synonym})

    assert list(hits)


def test_exact_match():
    doc = "whole onion"
    stopwords = ["whole"]
    term = ("onion",)

    index = HashedIXSearch(stopwords=stopwords)
    index.add(0, doc)

    assert index.query_exact(term) == 0


def test_exact_match_duplicate():
    doc = "whole onion"
    stopwords = ["whole"]
    term = ("onion",)

    index = HashedIXSearch()
    index.add(0, doc, stopwords=stopwords)
    index.add(0, doc, stopwords=stopwords)

    assert index.query_exact(term) == 0


def test_highlighting():
    doc = "five onions, diced"
    term = ("onion",)

    stemmer = NaivePluralStemmer()
    index = HashedIXSearch(stemmer=stemmer)
    markup = index.highlight(doc, [term])

    assert markup == "five <mark>onions</mark>, diced"


def test_highlighting_escaping():
    doc = "egg & bacon"
    terms = [("egg",), ("bacon",)]

    stemmer = NaivePluralStemmer()
    index = HashedIXSearch(stemmer=stemmer)
    markup = index.highlight(doc, terms)

    assert markup == "<mark>egg</mark> &amp; <mark>bacon</mark>"


def test_highlighting_unstemmed():
    doc = "one carrot"
    term = ("carrot",)

    index = HashedIXSearch()
    markup = index.highlight(doc, [term])

    assert markup == "one <mark>carrot</mark>"


def test_highlighting_case_insensitive_term():
    doc = "Wine"
    term = ("wine",)

    index = HashedIXSearch()
    markup = index.highlight(doc, [term], case_sensitive=False)

    assert markup == "<mark>Wine</mark>"


def test_highlighting_case_insensitive_phrase():
    doc = "Place in Dutch Oven, and leave for one hour"
    term = ("dutch", "oven")

    index = HashedIXSearch()
    markup = index.highlight(doc, [term], case_sensitive=False)

    assert markup == "Place in <mark>Dutch Oven</mark>, and leave for one hour"


def test_highlighting_partial_match_ignored():
    doc = "Place in Dutch oven, and leave for one hour"
    term = ("dutch", "oven")

    index = HashedIXSearch()
    markup = index.highlight(doc, [term])

    assert markup == "Place in Dutch oven, and leave for one hour"


def test_highlighting_repeat_match():
    doc = "daal daal daal"
    term = ("daal",)

    index = HashedIXSearch()
    markup = index.highlight(doc, [term])

    assert markup == "<mark>daal</mark> <mark>daal</mark> <mark>daal</mark>"


def test_highlighting_empty_terms():
    doc = "mushrooms"

    index = HashedIXSearch()
    markup = index.highlight(doc, [])

    assert markup == doc


def test_highlighting_term_larger_than_query():
    doc = "tofu"
    term = ("pack", "tofu",)

    stemmer = NaivePluralStemmer()
    index = HashedIXSearch(stemmer=stemmer)
    markup = index.highlight(doc, [term])

    assert markup == "tofu"


def test_phrase_term_highlighting():
    doc = "can of baked beans"
    term = ("baked", "bean")

    stemmer = NaivePluralStemmer()
    index = HashedIXSearch(stemmer=stemmer)
    markup = index.highlight(doc, [term])

    assert markup == "can of <mark>baked beans</mark>"


def test_trigram_phrase_term_highlighting():
    doc = "sliced red bell pepper as filling"
    term = ("red", "bell", "pepper")

    index = HashedIXSearch()
    markup = index.highlight(doc, [term])

    assert markup == "sliced <mark>red bell pepper</mark> as filling"


def test_synonym_highlighting():
    doc = "soymilk."
    term = ("soy", "milk")

    stemmer = NaivePluralStemmer()
    synonyms = {"soymilk": "soy milk"}
    index = HashedIXSearch(stemmer=stemmer, synonyms=synonyms)
    markup = index.highlight(doc, [term])

    assert markup == "<mark>soy milk</mark>."


def test_phrase_multi_term_highlighting():
    doc = "put the skewers in the frying pan"
    terms = [("skewer",), ("frying", "pan",)]
    expected = "put the <mark>skewers</mark> in the <mark>frying pan</mark>"

    stemmer = NaivePluralStemmer()
    index = HashedIXSearch(stemmer=stemmer)
    markup = index.highlight(doc, terms)

    assert markup == expected


def test_phrase_multi_term_highlighting_extra():
    doc = "put the kebab skewers in the pan"
    terms = [("kebab", "skewer",), ("pan",)]
    expected = "put the <mark>kebab skewers</mark> in the <mark>pan</mark>"

    stemmer = NaivePluralStemmer()
    index = HashedIXSearch(stemmer=stemmer)
    markup = index.highlight(doc, terms)

    assert markup == expected


def test_highlighting_non_ascii():
    doc = "60 ml crème fraîche"
    term = ("creme", "fraiche")

    stemmer = UnidecodeStemmer()
    index = HashedIXSearch(stemmer=stemmer)
    markup = index.highlight(doc, [term])

    assert markup == "60 ml <mark>crème fraîche</mark>"


def test_retain_numbers():
    doc = "preheat the oven to 300 degrees"
    terms = [("oven",), ("300",)]
    expected = "preheat the <mark>oven</mark> to <mark>300</mark> degrees"

    index = HashedIXSearch()
    markup = index.highlight(doc, terms)

    assert markup == expected


def test_retained_style():
    doc = "Step one, oven.  Phase two: pan."
    terms = [("oven",), ("pan",)]
    expected = "Step one, <mark>oven</mark>.  Phase two: <mark>pan</mark>."

    stemmer = NaivePluralStemmer()
    index = HashedIXSearch(stemmer=stemmer)
    markup = index.highlight(doc, terms)

    assert markup == expected


def test_ambiguous_prefix():
    doc = "food mill."
    terms = [("food", "processor"), ("food", "mill")]

    stemmer = NaivePluralStemmer()
    index = HashedIXSearch(stemmer=stemmer)
    markup = index.highlight(doc, terms)

    assert markup == "<mark>food mill</mark>."


def test_partial_suffix():
    doc = "medium onion"
    terms = [("onion", "gravy")]

    stemmer = NaivePluralStemmer()
    index = HashedIXSearch(stemmer=stemmer)
    markup = index.highlight(doc, terms)

    assert markup == "medium onion"


def test_term_attributes():
    doc = "garlic"
    term = ("garlic",)

    terms = [term]
    term_attributes = {term: {"id": "example"}}

    stemmer = NaivePluralStemmer()
    index = HashedIXSearch(stemmer=stemmer)
    markup = index.highlight(doc, terms, term_attributes=term_attributes)

    assert markup == '<mark id="example">garlic</mark>'


def test_hit_scoring():
    precise_match = "garlic"
    imprecise_match = "clove garlic"

    index = HashedIXSearch()
    index.add(0, precise_match)
    index.add(1, imprecise_match)

    hits = index.query("garlic")

    assert len(hits) == 2
    assert hits[0]['doc_id'] == 0


def test_term_frequency_tiebreaker():
    infrequent_doc = "clove"
    frequent_doc = "garlic"

    index = HashedIXSearch()
    index.add(0, infrequent_doc)
    index.add(1, frequent_doc, count=5)

    hits = index.query("garlic clove", query_limit=-1)

    assert len(hits) == 2
    assert hits[0]['doc_id'] == 1
