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


def _candidate_matches(token, terms):

    # Open an iterator over each candidate term's tokens
    candidates = {term: iter(term) for term in terms}

    # Narrow the list of candidates to those that continue to match
    candidates = {
        term: remaining_tokens
        for term, remaining_tokens in candidates.items()
        if next(remaining_tokens, None) == token
    }

    # Return the candidate terms along with copies of their token lists
    return {
        term: term
        for term in terms
        if term in candidates
    }


def _render_match(cstring, attributes):
    element = Element("mark", attributes or {})
    element.text = cstring.getvalue()
    return tostring(element, encoding="unicode")
