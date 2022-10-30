from string import punctuation


def _is_separator(token):
    if token.isspace():
        return True
    if not token.strip(punctuation):
        return True
    return False


def _render_match(match, attributes):
    attributes = attributes or {}
    attribs = "".join(f' {key}="{value}"' for key, value in attributes.items())
    return f"<mark{attribs}>{match}</mark>"
