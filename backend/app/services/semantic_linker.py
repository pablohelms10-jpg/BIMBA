from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

from app.config import settings
from app.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class LinkCandidate:
    audio_segment_id: str
    visual_frame_id: str
    similarity_score: float


class SemanticLinker:
    """
    Links audio segments to visual frames using cosine similarity of embeddings.

    Algorithm:
    1. Compute embeddings for all audio transcripts (batch).
    2. Compute embeddings for all OCR slide texts (batch).
    3. Build NxM cosine-similarity matrix.
    4. Threshold at settings.semantic_similarity_threshold.
    5. Return all (segment, frame, score) pairs above threshold.
    """

    def __init__(self) -> None:
        self._embed_svc = EmbeddingService()

    def compute_links(
        self,
        segments: List[Dict],   # [{"id": str, "transcript": str}, ...]
        frames: List[Dict],     # [{"id": str, "ocr_text": str}, ...]
    ) -> List[LinkCandidate]:
        """
        Compute semantic links between audio segments and visual frames.

        Args:
            segments: List of dicts with 'id' and 'transcript'.
            frames: List of dicts with 'id' and 'ocr_text'.

        Returns:
            List of LinkCandidate above threshold, sorted by score descending.
        """
        if not segments or not frames:
            logger.warning("No segments or frames to link.")
            return []

        # Filter out empty texts
        seg_texts = [s.get("transcript") or "" for s in segments]
        frame_texts = [f.get("ocr_text") or "" for f in frames]

        logger.info(
            "Computing embeddings for %d segments and %d frames",
            len(segments),
            len(frames),
        )

        seg_embeddings = self._embed_svc.embed_batch(seg_texts)
        frame_embeddings = self._embed_svc.embed_batch(frame_texts)

        seg_matrix = np.array(seg_embeddings, dtype=np.float32)   # [N, D]
        frame_matrix = np.array(frame_embeddings, dtype=np.float32)  # [M, D]

        # Cosine similarity matrix [N, M]
        # Since vectors are L2-normalized, dot product == cosine similarity
        similarity_matrix = np.dot(seg_matrix, frame_matrix.T)

        threshold = settings.semantic_similarity_threshold
        links: List[LinkCandidate] = []

        for i, seg in enumerate(segments):
            for j, frame in enumerate(frames):
                score = float(similarity_matrix[i, j])
                if score >= threshold:
                    links.append(
                        LinkCandidate(
                            audio_segment_id=seg["id"],
                            visual_frame_id=frame["id"],
                            similarity_score=score,
                        )
                    )

        links.sort(key=lambda lc: lc.similarity_score, reverse=True)
        logger.info(
            "Found %d semantic links above threshold %.2f", len(links), threshold
        )
        return links

    def best_frame_per_segment(
        self, links: List[LinkCandidate]
    ) -> Dict[str, LinkCandidate]:
        """Return the best (highest score) frame for each audio segment."""
        best: Dict[str, LinkCandidate] = {}
        for lc in sorted(links, key=lambda x: x.similarity_score, reverse=True):
            if lc.audio_segment_id not in best:
                best[lc.audio_segment_id] = lc
        return best

    def best_segments_per_frame(
        self, links: List[LinkCandidate], top_k: int = 3
    ) -> Dict[str, List[LinkCandidate]]:
        """Return the top-k audio segments for each visual frame."""
        groups: Dict[str, List[LinkCandidate]] = {}
        for lc in links:
            groups.setdefault(lc.visual_frame_id, []).append(lc)
        return {
            fid: sorted(cands, key=lambda x: x.similarity_score, reverse=True)[:top_k]
            for fid, cands in groups.items()
        }
