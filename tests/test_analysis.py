from hashedixsearch.analysis import (
    SynonymAnalyzer,
    WhitespacePunctuationTokenAnalyzer,
)


def test_whitespace_punctuation_analyzer_tokenization():
    doc = "coriander, chopped"

    analyzer = WhitespacePunctuationTokenAnalyzer()
    tokens = list(analyzer.process(doc))

    assert tokens == ["coriander", ",", " ", "chopped"]


def test_token_synonyms():
    doc = "soymilk."
    synonyms = {"soymilk": "soy milk"}

    analyzer = SynonymAnalyzer(synonyms=synonyms)
    tokens = list(analyzer.process(doc))

    assert tokens == ["soy", " ", "milk", "."]
