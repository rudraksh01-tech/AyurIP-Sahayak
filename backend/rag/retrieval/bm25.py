"""Okapi BM25 keyword search in pure Python.

Used as a keyword baseline and as one half of hybrid retrieval.
"""

import math
import re
from collections import Counter


TOKEN_PATTERN = re.compile(r"\w+")

STOPWORDS = frozenset(
    "a an and are as at be been by can do does for from has have how i in "
    "is it its me of on or that the their there these this to was were what "
    "when where which who why will with you your".split()
)


def tokenize(text):
    return [
        token
        for token in TOKEN_PATTERN.findall(text.lower())
        if len(token) > 1 and token not in STOPWORDS
    ]


class BM25:
    def __init__(self, corpus_tokens, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b

        self.term_frequencies = [Counter(tokens) for tokens in corpus_tokens]
        self.lengths = [len(tokens) for tokens in corpus_tokens]
        self.average_length = sum(self.lengths) / max(len(self.lengths), 1)

        document_frequency = Counter()

        for frequencies in self.term_frequencies:
            document_frequency.update(frequencies.keys())

        total = len(corpus_tokens)

        self.idf = {
            term: math.log(1 + (total - count + 0.5) / (count + 0.5))
            for term, count in document_frequency.items()
        }

    def scores(self, query_tokens):
        """Return one BM25 score per document, in corpus order."""
        query_terms = [term for term in set(query_tokens) if term in self.idf]
        results = []

        for frequencies, length in zip(self.term_frequencies, self.lengths):
            score = 0.0
            length_norm = 1 - self.b + self.b * length / self.average_length

            for term in query_terms:
                frequency = frequencies.get(term, 0)

                if frequency:
                    score += self.idf[term] * (
                        frequency * (self.k1 + 1)
                        / (frequency + self.k1 * length_norm)
                    )

            results.append(score)

        return results
