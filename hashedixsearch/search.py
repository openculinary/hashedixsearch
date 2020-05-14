from collections import defaultdict
from xml.sax.saxutils import escape

from hashedindex import HashedIndex
from hashedindex.textparser import (
    word_tokenize,
    NullStemmer,
)
from hashedixsearch._internal import (
    _candidate_matches,
    _is_separator,
    _ngram_to_term,
    SynonymAnalyzer,
)


def tokenize(
    doc,
    stopwords=None,
    ngrams=None,
    stemmer=None,
    synonyms=None,
    retain_casing=False,
    retain_punctuation=False,
    tokenize_whitespace=False,
):
    stopwords = stopwords or []
    ngrams = ngrams or 4
    stemmer = stemmer or NullStemmer()

    if synonyms:
        analyzer = SynonymAnalyzer(synonyms)
        doc = str().join(analyzer.process(doc))

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

    stopwords = stopwords or []
    for term in tokenize(
        doc=doc,
        stopwords=stopwords,
        stemmer=stemmer,
        synonyms=synonyms,
    ):
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

    query_count = 0
    for term in tokenize(
        doc=query,
        stopwords=stopwords,
        stemmer=stemmer,
        synonyms=synonyms,
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


def highlight(query, terms, stemmer=None, synonyms=None, case_sensitive=True):

    # If no terms are provided to match on, do not attempt highlighting
    if not terms:
        return escape(query)

    terms = {term: list(term) for term in terms}
    max_n = max(len(term) for term in terms.values())

    # Generate unstemmed ngrams of the maximum term length
    ngrams = []
    for tokens in tokenize(
        doc=query,
        ngrams=max_n,
        synonyms=synonyms,
        retain_casing=True,
        retain_punctuation=True,
        tokenize_whitespace=True,
    ):
        if len(tokens) < max_n:
            break
        ngrams.append(tokens)

    # If we did not generate any ngrams, do not attempt highlighting
    if not ngrams:
        return escape(query)

    # Tail the ngram list with ngrams of decreasing length
    final_ngram = ngrams[-1]
    for n in range(0, max_n):
        ngrams.append(final_ngram[n+1:])

    # Build up a marked-up representation of the original query
    tag = None
    markup = ""
    accumulator = ""

    for ngram in ngrams:

        # Stop when we reach an empty end-of-stream ngram
        if not ngram:
            break

        # Determine whether any of the highlighting terms match
        ngram_term = _ngram_to_term(ngram, stemmer, case_sensitive)

        if not tag and not _is_separator(ngram_term[0]):
            tag = _candidate_matches(ngram_term, terms)
            markup += accumulator
            accumulator = ""

        # Consume one token at a time
        accumulator += escape(ngram[0])
        emit = tag is None

        # Advance the match window of each candidate tag element
        if tag and not _is_separator(ngram_term[0]):
            tag = {
                term: tokens[1:]
                for term, tokens in tag.items()
                if tokens[0] == ngram_term[0]
            }

            # Close the markup when any term's tokens have been consumed
            if not all(tag.values()):
                accumulator = f"<mark>{accumulator}</mark>"
                emit = True
                tag = None

        # Output accumulated tokens when we encounter emit-points
        if emit:
            markup += accumulator
            accumulator = ""

    return markup + accumulator
