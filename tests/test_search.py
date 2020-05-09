from hashedixsearch.search import (
    build_search_index,
    add_to_search_index,
    execute_queries,
    execute_query,
    execute_query_exact,
    highlight,
    tokenize,
    NullStemmer,
)


class NaivePluralStemmer(NullStemmer):
    @staticmethod
    def stem(word):
        return word.rstrip("s")


def test_tokenize_stopwords():
    doc = "red bell pepper diced"
    stopwords = ["diced"]

    tokens = list(tokenize(doc=doc, stopwords=stopwords))

    assert tokens[0] == ("red", "bell", "pepper")


def test_token_stemming():

    doc = "onions"

    tokens = list(tokenize(doc=doc, stemmer=NaivePluralStemmer))

    assert tokens[0] == ("onion",)


def test_document_retrieval():
    doc = "mayonnaise"

    index = build_search_index()
    add_to_search_index(index, 0, doc)
    hits = execute_query(index, doc)

    assert list(hits)


def test_analysis_consistency():
    doc = "soymilk"
    synonym = "soy milk"

    index = build_search_index()
    add_to_search_index(index, 0, "soymilk", synonyms={doc: synonym})
    hits = execute_queries(index, ["soy milk"], synonyms={doc: synonym})

    assert list(hits)


def test_exact_match():
    doc = "whole onion"
    stopwords = ["whole"]

    index = build_search_index()
    add_to_search_index(index, 0, doc, stopwords)

    term = ("onion",)
    assert execute_query_exact(index, term) == 0


def test_exact_match_duplicate():
    doc = "whole onion"
    stopwords = ["whole"]

    index = build_search_index()
    add_to_search_index(index, 0, doc, stopwords)
    add_to_search_index(index, 0, doc, stopwords)

    term = ("onion",)
    assert execute_query_exact(index, term) == 0


def test_highlighting():
    doc = "five onions, diced"
    term = ("onion",)

    stemmer = NaivePluralStemmer()

    markup = highlight(doc, [term], stemmer)

    assert markup == "five <mark>onions</mark>, diced"


def test_highlighting_unstemmed():
    doc = "one carrot"
    term = ("carrot",)

    markup = highlight(doc, [term])

    assert markup == "one <mark>carrot</mark>"


def test_highlighting_case_insensitive_term():
    doc = "Wine"
    term = ("wine",)

    markup = highlight(doc, [term], case_sensitive=False)

    assert markup == "<mark>Wine</mark>"


def test_highlighting_case_insensitive_phrase():
    doc = "Place in Dutch Oven, and leave for one hour"
    term = ("dutch", "oven")

    markup = highlight(doc, [term], case_sensitive=False)

    assert markup == "Place in <mark>Dutch Oven</mark>, and leave for one hour"


def test_highlighting_partial_match_ignored():
    doc = "Place in Dutch oven, and leave for one hour"
    term = ("dutch", "oven")

    markup = highlight(doc, [term])

    assert markup == "Place in Dutch oven, and leave for one hour"


def test_highlighting_repeat_match():
    doc = "daal daal daal"
    term = ("daal",)

    markup = highlight(doc, [term])

    assert markup == "<mark>daal</mark> <mark>daal</mark> <mark>daal</mark>"


def test_highlighting_empty_terms():
    doc = "mushrooms"

    markup = highlight(doc, [])

    assert markup == doc


def test_highlighting_term_larger_than_query():
    doc = "tofu"
    term = ("pack", "tofu",)

    stemmer = NaivePluralStemmer()

    markup = highlight(doc, [term], stemmer)

    assert markup == "tofu"


def test_phrase_term_highlighting():
    doc = "can of baked beans"
    term = ("baked", "bean")

    stemmer = NaivePluralStemmer()

    markup = highlight(doc, [term], stemmer)

    assert markup == "can of <mark>baked beans</mark>"


def test_trigram_phrase_term_highlighting():
    doc = "sliced red bell pepper as filling"
    term = ("red", "bell", "pepper")

    markup = highlight(doc, [term])

    assert markup == "sliced <mark>red bell pepper</mark> as filling"


def test_synonym_highlighting():
    doc = "soymilk."
    term = ("soy", "milk")

    stemmer = NaivePluralStemmer()
    synonyms = {"soymilk": "soy milk"}

    markup = highlight(doc, [term], stemmer, synonyms)

    assert markup == "<mark>soy milk</mark>."


def test_phrase_multi_term_highlighting():
    doc = "put the skewers in the frying pan"
    terms = [("skewer",), ("frying", "pan",)]
    expected = "put the <mark>skewers</mark> in the <mark>frying pan</mark>"

    stemmer = NaivePluralStemmer()

    markup = highlight(doc, terms, stemmer)

    assert markup == expected


def test_phrase_multi_term_highlighting_extra():
    doc = "put the kebab skewers in the pan"
    terms = [("kebab", "skewer",), ("pan",)]
    expected = "put the <mark>kebab skewers</mark> in the <mark>pan</mark>"

    stemmer = NaivePluralStemmer()

    markup = highlight(doc, terms, stemmer)

    assert markup == expected


def test_retain_numbers():
    doc = "preheat the oven to 300 degrees"
    terms = [("oven",), ("300",)]
    expected = "preheat the <mark>oven</mark> to <mark>300</mark> degrees"

    markup = highlight(doc, terms, stemmer=None)

    assert markup == expected


def test_retained_style():
    doc = "Step one, oven.  Phase two: pan."
    terms = [("oven",), ("pan",)]
    expected = "Step one, <mark>oven</mark>.  Phase two: <mark>pan</mark>."

    stemmer = NaivePluralStemmer()

    markup = highlight(doc, terms, stemmer)

    assert markup == expected
