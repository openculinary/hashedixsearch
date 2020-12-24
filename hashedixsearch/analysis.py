import re
from string import punctuation


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
