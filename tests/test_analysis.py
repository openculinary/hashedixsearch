import unittest

from hashedixsearch.analysis import (
    SynonymAnalyzer,
    WhitespacePunctuationTokenAnalyzer,
)


class TestAnalysis(unittest.TestCase):
    def test_whitespace_punctuation_analyzer_tokenization(self):
        doc = "coriander, chopped"

        analyzer = WhitespacePunctuationTokenAnalyzer()
        tokens = list(analyzer.process(doc))

        assert tokens == ["coriander", ",", " ", "chopped"]

    def test_token_synonyms(self):
        doc = "soymilk."
        synonyms = {"soymilk": "soy milk"}

        analyzer = SynonymAnalyzer(synonyms=synonyms)
        tokens = list(analyzer.process(doc))

        assert tokens == ["soy", " ", "milk", "."]
