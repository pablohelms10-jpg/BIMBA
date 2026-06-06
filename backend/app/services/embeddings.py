from __future__ import annotations

import logging
from typing import List

import numpy as np

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingService:
    """Text embedding using sentence-transformers (all-MiniLM-L6-v2)."""

    def __init__(self) -> None:
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # type: ignore

            logger.info("Loading sentence-transformers model: %s", MODEL_NAME)
            self._model = SentenceTransformer(MODEL_NAME)
        return self._model

    def embed(self, text: str) -> List[float]:
        """Embed a single text string. Returns a list of floats."""
        model = self._get_model()
        vec = model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        """Embed a list of texts in batches. Returns list of embedding vectors."""
        if not texts:
            return []
        model = self._get_model()
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vectors]

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors (both assumed L2-normalized)."""
        va = np.array(a, dtype=np.float32)
        vb = np.array(b, dtype=np.float32)
        return float(np.dot(va, vb))
