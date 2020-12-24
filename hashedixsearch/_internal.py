import re
from string import punctuation
from xml.etree.ElementTree import Element, tostring


class WhitespacePunctuationTokenAnalyzer:

    delimiters = rf"([\s+|{punctuation}])"

    def process(self, input):
        for token in re.split(self.delimiters, input):
            yield from self.analyze_token(token)

    def analyze_token(self, token):
        if token:
            yield token


class SynonymAnalyzer(WhitespacePunctuationTokenAnalyzer):
    def __init__(self, synonyms):
        self.synonyms = synonyms

    def analyze_token(self, token):
        token = self.synonyms.get(token) or token
        if token:
            yield from re.split(r"(\s+)", token)


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
    candidates = {term: iter(term_tokens) for term, term_tokens in terms.items()}

    # Step through the input ngram
    while ngram_token := next(ngram_tokens, None):

        # Skip past separator tokens
        while _is_separator(ngram_token):
            ngram_token = next(ngram_tokens, None)
        if not ngram_token:
            break

        # Narrow the list of candidates to those that continue to match
        candidates = {
            term: term_tokens
            for term, term_tokens in candidates.items()
            if next(term_tokens, None) == ngram_token
        }

    # Return the candidate terms along with copies of their token lists
    return {
        term: list(term_tokens)
        for term, term_tokens in terms.items()
        if term in candidates
    }


def _render_match(text, attributes):
    element = Element("mark", attributes or {})
    element.text = text
    return tostring(element, encoding="unicode")
