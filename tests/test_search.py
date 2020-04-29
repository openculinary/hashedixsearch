from hashedixsearch import (
    build_search_index,
    add_to_search_index,
    execute_queries,
    execute_query,
    execute_query_exact,
    highlight,
    tokenize,
    NullAnalyzer,
    NullStemmer,
    SynonymAnalyzer,
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


def test_null_analyzer_tokenization():
    doc = "coriander, chopped"

    analyzer = NullAnalyzer()
    tokens = list(analyzer.process(doc))

    assert tokens == ["coriander", "chopped"]


def test_token_synonyms():
    doc = "soymilk"
    synonyms = {"soymilk": "soy milk"}

    analyzer = SynonymAnalyzer(synonyms=synonyms)
    tokens = list(tokenize(doc=doc, analyzer=analyzer))

    assert tokens == [("soy", "milk"), ("soy",), ("milk",), ()]


def test_document_retrieval():
    doc = "mayonnaise"

    index = build_search_index()
    add_to_search_index(index, 0, doc)
    hits = execute_query(index, doc)

    assert list(hits)


def test_analysis_consistency():
    doc = "soymilk"
    synonym = "soy milk"
    analyzer = SynonymAnalyzer(synonyms={doc: synonym})

    index = build_search_index()
    add_to_search_index(index, 0, "soymilk", analyzer=analyzer)
    hits = execute_queries(index, ["soy milk"], analyzer=analyzer)

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
    analyzer = NullAnalyzer()

    markup = highlight(doc, [term], stemmer, analyzer)

    assert markup == "five <mark>onions</mark> diced"


def test_phrase_term_highlighting():
    doc = "can of baked beans"
    term = ("baked", "bean")

    stemmer = NaivePluralStemmer()
    analyzer = NullAnalyzer()

    markup = highlight(doc, [term], stemmer, analyzer)

    assert markup == "can of <mark>baked beans</mark>"


def test_phrase_multi_term_highlighting():
    doc = "put the skewers in the frying pan"
    terms = [("skewer",), ("frying", "pan",)]
    expected = "put the <mark>skewers</mark> in the <mark>frying pan</mark>"

    stemmer = NaivePluralStemmer()
    analyzer = NullAnalyzer()

    markup = highlight(doc, terms, stemmer, analyzer)

    assert markup == expected


def test_phrase_multi_term_highlighting_extra():
    doc = "put the kebab skewers in the pan"
    terms = [("kebab", "skewer",), ("pan",)]
    expected = "put the <mark>kebab skewers</mark> in the <mark>pan</mark>"

    stemmer = NaivePluralStemmer()
    analyzer = NullAnalyzer()

    markup = highlight(doc, terms, stemmer, analyzer)

    assert markup == expected
