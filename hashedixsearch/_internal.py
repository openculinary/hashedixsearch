from string import punctuation

import hashedixsearch.search


def _ngram_to_term(ngram, stemmer):
    text = "".join(ngram)
    return next(hashedixsearch.search.tokenize(
        doc=text,
        stemmer=stemmer,
        retain_casing=True,
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


def _longest_prefix(ngram, terms):
    longest_term = []
    for term in terms.values():

        # Open iterators over the ngram and term tokens
        ngram_tokens = iter(ngram)
        term_tokens = iter(term)

        ngram_token = next(ngram_tokens, None)
        term_token = next(term_tokens, None)

        # Never consider an ngram that begins with a separator as a match
        if _is_separator(ngram_token):
            break

        # Consume from the ngram and term streams in parallel
        while ngram_token and term_token:
            if ngram_token == term_token:
                ngram_token = next(ngram_tokens, None)
                term_token = next(term_tokens, None)
            if _is_separator(ngram_token):
                ngram_token = next(ngram_tokens, None)
            term_token = next(term_tokens, None)

        # If the ngram stream was fully consumed, record the longest term
        if ngram_token is None and len(term) > len(longest_term):
            longest_term = term

    return longest_term
