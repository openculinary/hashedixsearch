import re
from string import punctuation

import hashedixsearch.search


class WhitespacePunctuationTokenAnalyzer:

    delimiters = rf'([\s+|{punctuation}])'

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


def _ngram_to_term(ngram, stemmer, case_sensitive):
    text = "".join(ngram)
    return next(hashedixsearch.search.tokenize(
        doc=text,
        stemmer=stemmer,
        retain_casing=case_sensitive,
        retain_punctuation=True,
        tokenize_whitespace=True
    ))


def _is_separator(token):
    if token is None:
        return False
    if token.isspace():
        return True
    if token.strip(punctuation) == str():
        return True
    return False


def _candidate_matches(ngram, terms):

    # Never consider an ngram that begins with a separator as a match
    if _is_separator(ngram[0]):
        return

    # Open an iterator over the ngram terms
    ngram_tokens = iter(ngram)

    # Open an iterator over each candidate term's tokens
    candidates = {
        term: iter(term_list)
        for term, term_list in terms.items()
    }

    # Continue while candidates remain
    while candidates:

        # Skip past whitespace in the ngram tokens
        ngram_token = next(ngram_tokens, None)
        while _is_separator(ngram_token):
            ngram_token = next(ngram_tokens, None)
        if not ngram_token:
            break

        # Advance the iterator for each candidate term
        candidates = {
            term: term_tokens
            for term, term_tokens in candidates.items()
            if next(term_tokens, None) == ngram_token
        }

    # Return the candidates, with copies of the token list
    return {
        candidate: list(terms[candidate])
        for candidate in candidates
    }
