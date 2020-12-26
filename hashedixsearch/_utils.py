from string import punctuation
from xml.etree.ElementTree import Element, tostring


def _is_separator(token):
    if token.isspace():
        return True
    if token.strip(punctuation) == str():
        return True
    return False


def _render_match(cstring, attributes):
    element = Element("mark", attributes or {})
    element.text = cstring.getvalue()
    return tostring(element, encoding="unicode")
