"""
Production embedder implementation, pending model selection.

Candidate options:
  - Hosted embedding API (e.g. OpenAI, Anthropic) — no infrastructure
    to run, cost scales per call
  - Local open-source model (e.g. sentence-transformers) — no
    per-call cost, requires hosting

The chosen implementation must return vectors of a fixed dimension on
every call, matching self.dimensions, since the vector store schema
depends on a constant embedding size.

Remaining work once a provider is selected:
  - implement the API call / model invocation in embed()
  - set `dimensions` to match the model's output size
    (e.g. 1536 for OpenAI text-embedding-3-small, 384 for many
    sentence-transformers models)
"""

from pipeline.embedder_base import Embedder


class RealEmbedder(Embedder):
    def __init__(self, model_name: str, dimensions: int):
        self.model_name = model_name
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        # TODO: call the embedding API/model, e.g.:
        #
        #   response = client.embeddings.create(model=self.model_name, input=texts)
        #   return [item.embedding for item in response.data]
        #
        raise NotImplementedError("Embedding model not yet integrated.")
