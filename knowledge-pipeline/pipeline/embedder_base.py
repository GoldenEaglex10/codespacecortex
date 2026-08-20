"""
Embedder interface.

Downstream components (vector store, search) depend only on this
interface, allowing the embedding implementation to be replaced
without changes elsewhere in the pipeline.
"""

from abc import ABC, abstractmethod


class Embedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Turn a list of strings into a list of vectors (same order)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Length of each embedding vector this embedder produces."""
        raise NotImplementedError
