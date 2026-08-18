"""
Placeholder embedder implementation, used until a production embedding
model is integrated.

Uses a hashing bag-of-words vectorizer: each token is hashed into one
of N buckets, and the resulting vector is a normalized count of token
occurrences per bucket. This produces genuine similarity signal based
on vocabulary overlap — chunks sharing words score as similar, chunks
on unrelated topics score as dissimilar — which is sufficient for
testing retrieval mechanics, tenant filtering, and ranking logic.

Limitation: this is lexical overlap, not semantic similarity (e.g. it
will not associate "loop" with "iteration"). A production embedding
model is required before search quality can be meaningfully evaluated.
"""

import re
import math
from collections import Counter
from pipeline.embedder_base import Embedder

DEFAULT_DIMENSIONS = 256


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class FakeEmbedder(Embedder):
    def __init__(self, dimensions: int = DEFAULT_DIMENSIONS):
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        tokens = _tokenize(text)
        counts = Counter(tokens)

        for token, count in counts.items():
            bucket = hash(token) % self._dimensions
            vector[bucket] += count

        # L2-normalize so cosine similarity is not skewed by chunk
        # length (raw counts would otherwise favor longer chunks).
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector
