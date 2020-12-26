from collections import defaultdict
from io import StringIO
from xml.sax.saxutils import escape

from hashedindex import HashedIndex
from hashedindex.textparser import NullStemmer, word_tokenize

from hashedixsearch.analysis import SynonymAnalyzer
from hashedixsearch._utils import (
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

    def _next_token(self, ngram, case_sensitive):
        return next(
            self.tokenize(
                doc=str().join(ngram),
                retain_casing=case_sensitive,
                retain_punctuation=True,
                retain_whitespace=True,
            )
        )[0]

    def highlight(self, doc, terms, case_sensitive=True, term_attributes=None):
        # If no terms are provided to match on, do not attempt highlighting
        if not terms:
            return escape(doc)

        max_n = max(len(term) for term in terms)
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

        # Remove the end-of-stream ngram
        ngrams.pop()

        # Build up a marked-up representation of the original document
        candidates = {}
        accumulator = StringIO()
        markup = StringIO()

        for ngram in ngrams:

            # Consume one token at a time
            token = self._next_token(ngram, case_sensitive)

            # Advance the match window for each candidate term
            if not _is_separator(token):
                candidates = {
                    term: term[1:]
                    for term in candidates.values() or terms
                    if term[0] == token
                }

            # Prepare the current token for output, and write it to the
            # accumulator buffer if we are within candidate highlight tokens
            output = escape(ngram[0])
            if candidates:
                accumulator.write(output)

            # Render highlight markup once a candidate's terms are consumed
            emit = next(filter(lambda k: not candidates[k], candidates), None)
            if emit:
                attributes = term_attributes.get(emit)
                output = _render_match(accumulator, attributes)
                candidates = {}
                accumulator = StringIO()

            # Write output to the markup stream when match candidates are empty
            if not candidates:
                markup.write(output)

        markup.write(accumulator.getvalue())
        return markup.getvalue()
