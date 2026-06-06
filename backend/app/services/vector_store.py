from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

SEGMENT_TYPE = "audio_segment"
FRAME_TYPE = "visual_frame"


class VectorStoreService:
    """Qdrant vector store for audio segment and visual frame embeddings."""

    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client is None:
            from qdrant_client import QdrantClient  # type: ignore
            from qdrant_client.models import Distance, VectorParams  # type: ignore

            self._client = QdrantClient(url=settings.qdrant_url)
            self._ensure_collection()
        return self._client

    def _ensure_collection(self) -> None:
        from qdrant_client.models import Distance, VectorParams  # type: ignore

        client = self._client
        collections = [c.name for c in client.get_collections().collections]
        if settings.qdrant_collection not in collections:
            client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(
                    size=settings.embedding_dim,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection: %s", settings.qdrant_collection)

    def upsert_segment_embedding(
        self,
        segment_id: str,
        document_id: str,
        vector: List[float],
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store embedding for an audio segment."""
        from qdrant_client.models import PointStruct  # type: ignore

        client = self._get_client()
        meta = {"type": SEGMENT_TYPE, "document_id": document_id, **(payload or {})}
        client.upsert(
            collection_name=settings.qdrant_collection,
            points=[PointStruct(id=segment_id, vector=vector, payload=meta)],
        )

    def upsert_frame_embedding(
        self,
        frame_id: str,
        document_id: str,
        vector: List[float],
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store embedding for a visual frame."""
        from qdrant_client.models import PointStruct  # type: ignore

        client = self._get_client()
        meta = {"type": FRAME_TYPE, "document_id": document_id, **(payload or {})}
        client.upsert(
            collection_name=settings.qdrant_collection,
            points=[PointStruct(id=frame_id, vector=vector, payload=meta)],
        )

    def search_similar(
        self,
        query_vector: List[float],
        document_id: str,
        result_type: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors filtered by document_id and type."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue  # type: ignore

        client = self._get_client()
        results = client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(key="document_id", match=MatchValue(value=document_id)),
                    FieldCondition(key="type", match=MatchValue(value=result_type)),
                ]
            ),
            limit=top_k,
            with_payload=True,
        )
        return [{"id": r.id, "score": r.score, "payload": r.payload} for r in results]

    def delete_document_vectors(self, document_id: str) -> None:
        """Remove all vectors associated with a document."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue  # type: ignore

        client = self._get_client()
        client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            ),
        )
        logger.info("Deleted all vectors for document %s", document_id)
