from string import punctuation
from xml.etree.ElementTree import Element, tostring


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

    # Open an iterator over each candidate term's tokens
    candidates = {term: iter(tokens) for term, tokens in terms.items()}

    # Step through the input ngram
    tokens = iter(ngram)
    while token := next(tokens, None):

        # Skip past separator tokens
        while _is_separator(token):
            token = next(tokens, None)
        if not token:
            break

        # Narrow the list of candidates to those that continue to match
        candidates = {
            term: remaining_tokens
            for term, remaining_tokens in candidates.items()
            if next(remaining_tokens, None) == token
        }

    # Return the candidate terms along with copies of their token lists
    return {
        term: list(remaining_tokens)
        for term, remaining_tokens in terms.items()
        if term in candidates
    }


def _render_match(text, attributes):
    element = Element("mark", attributes or {})
    element.text = text
    return tostring(element, encoding="unicode")
