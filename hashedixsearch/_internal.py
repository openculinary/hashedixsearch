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


def _longest_prefix(ngram, terms):
    prefix_length = 0
    for term, n in terms.items():
        term = iter(term)
        matches = not ngram[0].isspace()
        for idx, token in enumerate(ngram):
            if idx == n:
                break
            if token.isspace():
                idx += 1
                n += 1
                continue
            if token == next(term):
                idx += 1
                continue
            matches = False
        if matches and n > prefix_length:
            prefix_length = n
    return prefix_length
