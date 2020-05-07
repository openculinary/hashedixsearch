from collections import defaultdict
import re
from string import punctuation

from hashedindex import HashedIndex
from hashedindex.textparser import (
    word_tokenize,
    NullStemmer,
)
from hashedixsearch._internal import (
    _longest_prefix,
    _ngram_to_term,
)


class NullAnalyzer:
    def process(self, input):
        return input


class WhitespaceTokenAnalyzer:

    remove_punctuation = str.maketrans("", "", punctuation)

    def process(self, input):
        for token in input.split(" "):
            token = token.translate(self.remove_punctuation)
            for result in self.analyze_token(token):
                yield result

    def analyze_token(self, token):
        yield token


class WhitespacePunctuationTokenAnalyzer:

    delimiters = rf'([ {punctuation}])'

    def process(self, input):
        for token in re.split(self.delimiters, input):
            for analyzed_token in self.analyze_token(token):
                if analyzed_token:
                    yield analyzed_token

    def analyze_token(self, token):
        yield token


class SynonymAnalyzer(WhitespacePunctuationTokenAnalyzer):
    def __init__(self, synonyms):
        self.synonyms = synonyms

    def analyze_token(self, token):
        synonym = self.synonyms.get(token) or token
        for token in re.split(r"(\s+)", synonym):
            yield token


def tokenize(
    doc,
    stopwords=None,
    ngrams=None,
    stemmer=None,
    retain_casing=False,
    retain_punctuation=False,
    tokenize_whitespace=False,
):
    stopwords = stopwords or []
    ngrams = ngrams or 4
    stemmer = stemmer or NullStemmer()

    for ngrams in range(ngrams, 0, -1):
        for term in word_tokenize(
            text=doc,
            stopwords=stopwords,
            ngrams=ngrams,
            stemmer=stemmer,
            ignore_numeric=False,
            retain_casing=retain_casing,
            retain_punctuation=retain_punctuation,
            tokenize_whitespace=tokenize_whitespace,
        ):
            yield term

    # Produce an end-of-stream marker
    yield tuple()


def add_to_search_index(
    index, doc_id, doc, stopwords=None, stemmer=None, synonyms=None
):
    if synonyms:
        analyzer = SynonymAnalyzer(synonyms)
        doc = str().join(analyzer.process(doc))

    stopwords = stopwords or []
    for term in tokenize(doc=doc, stopwords=stopwords, stemmer=stemmer):
        if term:
            index.add_term_occurrence(term, doc_id)


def build_search_index():
    return HashedIndex()


def execute_queries(
    index, queries, stopwords=None, stemmer=None, synonyms=None, query_limit=1
):
    for query in queries:
        hits = execute_query(
            index=index,
            query=query,
            stopwords=stopwords,
            stemmer=stemmer,
            synonyms=synonyms,
            query_limit=query_limit,
        )
        if hits:
            yield query, hits


def execute_query(
    index, query, stopwords=None, stemmer=None, synonyms=None, query_limit=1
):
    hits = defaultdict(lambda: 0)
    terms = defaultdict(lambda: [])

    if synonyms:
        analyzer = SynonymAnalyzer(synonyms)
        query = str().join(analyzer.process(query))

    query_count = 0
    for term in tokenize(doc=query, stopwords=stopwords, stemmer=stemmer):
        query_count += 1
        try:
            for doc_id in index.get_documents(term):
                doc_length = index.get_document_length(doc_id)
                hits[doc_id] += len(term) / doc_length
                terms[doc_id].append(term)
        except IndexError:
            pass
        if query_count == query_limit:
            break
    hits = [
        {"doc_id": doc_id, "score": score, "terms": terms[doc_id]}
        for doc_id, score in hits.items()
    ]
    return sorted(hits, key=lambda hit: hit["score"], reverse=True)


def execute_query_exact(index, term):
    if term not in index:
        return
    for doc_id in index.get_documents(term):
        frequency = index.get_term_frequency(term, doc_id)
        doc_length = index.get_document_length(doc_id)
        if frequency == doc_length:
            return doc_id


def highlight(query, terms, stemmer=None, synonyms=None):
    terms = {term: len(term) for term in terms}
    max_n = max(n for n in terms.values())

    if synonyms:
        analyzer = SynonymAnalyzer(synonyms)
        query = str().join(analyzer.process(query))

    # Generate unstemmed ngrams of the maximum term length
    ngrams = []
    for tokens in tokenize(
        doc=query,
        ngrams=max_n,
        retain_casing=True,
        retain_punctuation=True,
        tokenize_whitespace=True,
    ):
        if len(tokens) < max_n:
            break
        ngrams.append(tokens)

    # If we did not generate any ngrams, do not attempt highlighting
    if not ngrams:
        return query

    # Tail the ngram list with ngrams of decreasing length
    final_ngram = ngrams[-1]
    for n in range(0, max_n):
        ngrams.append(final_ngram[n+1:])

    # Build up a marked-up representation of the original query
    tag = 0
    markup = ""
    for ngram in ngrams:

        # Advance through the text closing tags after their words are consumed
        tag -= 1
        if tag == 0:
            markup += "</mark>"

        # Stop when we reach an empty end-of-stream ngram
        if not ngram:
            break

        # Determine whether any of the highlighting terms match
        ngram_term = _ngram_to_term(ngram, stemmer)
        prefix_length = _longest_prefix(ngram_term, terms)

        # Begin markup if a prefix match was found
        if prefix_length:
            markup += f"<mark>"
            tag = prefix_length

        # Consume one token at a time
        markup += f"{ngram[0]}"

    return markup
