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
    ngram_length = len(ngram)
    for term, n in terms.items():

        idx = 0
        term = iter(term)
        matches = not ngram[idx].isspace()

        while matches and idx < min(n, ngram_length):
            if ngram[idx].isspace():
                idx += 1
                n += 1
                continue
            if ngram[idx] == next(term):
                idx += 1
                continue
            matches = False

        if matches and n > prefix_length:
            prefix_length = n
    return prefix_length
