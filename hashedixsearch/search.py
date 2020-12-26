from collections import defaultdict
from io import StringIO
from xml.sax.saxutils import escape

from hashedindex import HashedIndex
from hashedindex.textparser import NullStemmer, word_tokenize

from hashedixsearch.analysis import SynonymAnalyzer
from hashedixsearch._utils import (
    _candidate_matches,
    _is_separator,
    _render_match,
)


class HashedIXSearch(object):
    def __init__(
        self,
        ngrams=4,
        stemmer=None,
        stopwords=None,
        synonyms=None,
        retain_casing=False,
        retain_punctuation=False,
        retain_whitespace=False,
    ):
        self.index = HashedIndex()
        self.ngrams = ngrams
        self.stemmer = stemmer
        self.stopwords = stopwords
        self.synonyms = synonyms
        self.retain_casing = retain_casing
        self.retain_punctuation = retain_punctuation
        self.retain_whitespace = retain_whitespace

    def tokenize(self, doc, **kwargs):
        ngrams = kwargs.get("ngrams", self.ngrams)
        stemmer = kwargs.get("stemmer", self.stemmer)
        stopwords = kwargs.get("stopwords", self.stopwords)
        synonyms = kwargs.get("synonyms", self.synonyms)
        retain_casing = kwargs.get("retain_casing", self.retain_casing)
        retain_punctuation = kwargs.get("retain_punctuation", self.retain_punctuation)
        retain_whitespace = kwargs.get("retain_whitespace", self.retain_whitespace)

        if synonyms:
            analyzer = SynonymAnalyzer(synonyms)
            doc = str().join(analyzer.process(doc))

        for ngrams in range(ngrams, 0, -1):
            yield from word_tokenize(
                text=doc,
                ngrams=ngrams,
                stemmer=stemmer,
                stopwords=stopwords or [],
                ignore_numeric=False,
                retain_casing=retain_casing,
                retain_punctuation=retain_punctuation,
                tokenize_whitespace=retain_whitespace,
            )

        # Produce an end-of-stream marker
        yield tuple()

    def add(self, doc_id, doc, **kwargs):
        count = kwargs.pop("count", 1)
        tokens = self.tokenize(doc=doc, **kwargs)
        while term := next(tokens):
            self.index.add_term_occurrence(term, doc_id, count=count)

    def query(self, query, query_limit=1, **kwargs):
        count = defaultdict(lambda: 0)
        hits = defaultdict(lambda: 0)
        terms = defaultdict(lambda: [])

        for query_count, term in enumerate(self.tokenize(doc=query, **kwargs)):
            if query_count == query_limit:
                break
            try:
                doc_ids = self.index.get_documents(term)
            except IndexError:
                continue
            for doc_id in doc_ids:
                doc_length = self.index.get_document_length(doc_id)
                tf = self.index.get_term_frequency(term, doc_id)
                count[doc_id] += tf
                hits[doc_id] += len(term) * tf / doc_length
                terms[doc_id].append(term)
        return sorted(
            [
                {
                    "doc_id": doc_id,
                    "score": score,
                    "terms": terms[doc_id],
                    "count": count[doc_id],
                }
                for doc_id, score in hits.items()
            ],
            key=lambda x: (x["score"], x["count"]),
            reverse=True,
        )

    def query_batch(self, query_batch, **kwargs):
        for query in query_batch:
            yield query, self.query(query, **kwargs)

    def query_exact(self, term):
        if term not in self.index:
            return
        for doc_id in self.index.get_documents(term):
            frequency = self.index.get_term_frequency(term, doc_id)
            doc_length = self.index.get_document_length(doc_id)
            if frequency == doc_length:
                return doc_id

    def _ngram_to_term(self, ngram, case_sensitive):
        return next(
            self.tokenize(
                doc=str().join(ngram),
                retain_casing=case_sensitive,
                retain_punctuation=True,
                retain_whitespace=True,
            )
        )

    def highlight(self, doc, terms, case_sensitive=True, term_attributes=None):
        # If no terms are provided to match on, do not attempt highlighting
        if not terms:
            return escape(doc)

        terms = {term: list(term) for term in terms}
        max_n = max(len(term) for term in terms.values())
        term_attributes = term_attributes or {}

        # Generate unstemmed ngrams of the maximum term length
        ngrams = []
        for tokens in self.tokenize(
            doc=doc,
            ngrams=max_n,
            stemmer=NullStemmer(),
            retain_casing=True,
            retain_punctuation=True,
            retain_whitespace=True,
        ):
            if len(tokens) < max_n:
                break
            ngrams.append(tokens)

        # If we did not generate any ngrams, do not attempt highlighting
        if not ngrams:
            return escape(doc)

        # Tail the ngram list with ngrams of decreasing length
        final_ngram = ngrams[-1]
        for n in range(1, max_n + 1):
            ngrams.append(final_ngram[n:])

        # Build up a marked-up representation of the original document
        candidates = {}
        accumulator = None
        markup = StringIO()

        ngrams = iter(ngrams)
        while ngram := next(ngrams):

            # Check for candidate term highlighting matches
            ngram_term = self._ngram_to_term(ngram, case_sensitive)
            if not candidates and not _is_separator(ngram_term[0]):
                candidates = _candidate_matches(ngram_term, terms)
                accumulator = StringIO()

            # Consume one token at a time
            token = escape(ngram[0])
            if candidates:
                accumulator.write(token)

            # Advance the match window for each candidate term
            if not _is_separator(ngram_term[0]):
                candidates = {
                    term: tokens[1:]
                    for term, tokens in candidates.items()
                    if tokens[0] == ngram_term[0]
                }

            # Render highlight markup once a candidate's terms are consumed
            for closing_term, remaining_tokens in candidates.items():
                if remaining_tokens:
                    continue
                attributes = term_attributes.get(closing_term)
                token = _render_match(accumulator, attributes)
                candidates = {}
                accumulator = None
                break

            # Write tokens to the output stream
            if not candidates:
                markup.write(token)

        if accumulator:
            markup.write(accumulator.getvalue())
        return markup.getvalue()
