from collections import defaultdict
from string import punctuation

from hashedindex import HashedIndex
from hashedindex.textparser import (
    word_tokenize,
    NullStemmer,
)


class NullAnalyzer:

    remove_punctuation = str.maketrans("", "", punctuation)

    def process(self, input):
        for token in input.split(" "):
            token = token.translate(self.remove_punctuation)
            for result in self.analyze_token(token):
                yield result

    def analyze_token(self, token):
        yield token


class SynonymAnalyzer(NullAnalyzer):
    def __init__(self, synonyms):
        self.synonyms = synonyms

    def analyze_token(self, token):
        synonym = self.synonyms.get(token) or token
        for token in synonym.split(" "):
            yield token


def tokenize(doc, stopwords=None, ngrams=None, stemmer=None, analyzer=None):
    stopwords = stopwords or []
    stemmer = stemmer or NullStemmer()
    analyzer = analyzer or NullAnalyzer()

    words = list(analyzer.process(doc))
    word_count = len(words)
    doc = " ".join(words)

    ngrams = ngrams or word_count
    ngrams = min(ngrams, word_count, 4)
    ngrams = max(ngrams, 1)

    for ngrams in range(ngrams, 0, -1):
        for term in word_tokenize(doc, stopwords, ngrams, stemmer=stemmer):
            yield term

    # Produce an end-of-stream marker
    yield tuple()


def add_to_search_index(
    index, doc_id, doc, stopwords=None, stemmer=None, analyzer=None
):
    stopwords = stopwords or []
    for term in tokenize(
        doc=doc, stopwords=stopwords, stemmer=stemmer, analyzer=analyzer
    ):
        if term:
            index.add_term_occurrence(term, doc_id)


def build_search_index():
    return HashedIndex()


def execute_queries(
    index, queries, stopwords=None, stemmer=None, analyzer=None, query_limit=1
):
    for query in queries:
        hits = execute_query(
            index=index,
            query=query,
            stopwords=stopwords,
            stemmer=stemmer,
            analyzer=analyzer,
            query_limit=query_limit,
        )
        if hits:
            yield query, hits


def execute_query(
    index, query, stopwords=None, stemmer=None, analyzer=None, query_limit=1
):
    hits = defaultdict(lambda: 0)
    terms = defaultdict(lambda: [])
    query_count = 0
    for term in tokenize(
        query, stopwords=stopwords, stemmer=stemmer, analyzer=analyzer
    ):
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


def ngram_to_term(ngram, stemmer, analyzer):
    text = " ".join(ngram)
    return next(tokenize(doc=text, stemmer=stemmer, analyzer=analyzer))


def find_best_match(ngram, terms):
    best = (None, 0)
    for term, n in terms.items():
        if len(ngram) < n:
            continue
        matches = True
        for idx, subterm in enumerate(term):
            matches = matches and ngram[idx] == subterm
        if matches and n > best[1]:
            best = (term, n)
    return best


def highlight(query, terms, stemmer, analyzer):
    terms = {
        term: len(term)
        for term in terms
    }
    max_n = max(n for n in terms.values())

    # Generate unstemmed ngrams of the maximum term length
    ngrams = []
    for tokens in tokenize(doc=query, ngrams=max_n, analyzer=analyzer):
        if len(tokens) < max_n:
            break
        ngrams.append(tokens)

    # Tail the ngram list with ngrams of decreasing length
    final_ngram = ngrams[-1]
    for n in range(0, max_n):
        ngrams.append(final_ngram[n + 1:])

    # Build up a marked-up representation of the original query
    tag = 0
    markup = ''
    for ngram in ngrams:

        # Advance through the text closing tags after their words are consumed
        tag -= 1
        if tag == 0:
            markup += "</mark>"

        # Stop when we reach an empty end-of-stream ngram
        if not ngram:
            break
        if markup:
            markup += " "

        # Determine whether any of the highlighting terms match
        ngram_term = ngram_to_term(ngram, stemmer, analyzer)
        term, n = find_best_match(ngram_term, terms)

        # Begin markup if a match was found, and consume the next word token
        if term:
            markup += f"<mark>"
            tag = n
        markup += f"{ngram[0]}"

    return markup
