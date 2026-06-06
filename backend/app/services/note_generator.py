from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a medical note scribe for a university student.
Your task is to generate structured, hierarchical study notes from the provided class transcript and slide content.

STRICT RULES:
1. Generate notes ONLY from the provided transcript and slide content.
2. DO NOT add external information, definitions, or concepts not mentioned in the sources.
3. DO NOT invent clinical cases, drug names, or statistics.
4. DO NOT correct the professor — transcribe their ideas faithfully.
5. DO NOT paraphrase into a textbook style — preserve the professor's emphasis and structure.
6. If the transcript is empty or unclear for a section, write "[Sin transcripción disponible]".
7. Output MUST be valid JSON matching the specified schema.
"""

SECTION_PROMPT_TEMPLATE = """Given the following class slide and audio transcript, generate structured study notes in JSON format.

SLIDE TITLE: {slide_title}
SLIDE OCR TEXT:
{slide_ocr}

AUDIO TRANSCRIPT (timestamps {ts_start:.0f}s - {ts_end:.0f}s):
{transcript}

Output a JSON object with this exact schema:
{{
  "title": "<section title derived from slide or transcript>",
  "content": "<detailed notes as markdown>",
  "key_concepts": ["<concept1>", "<concept2>", ...],
  "summary": "<1-2 sentence summary>"
}}

Remember: ONLY use information from the transcript and slide. Do not add external knowledge."""


class NoteGeneratorService:
    """Claude-powered structured note generation from linked audio+visual content."""

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def generate_section_note(
        self,
        slide_title: Optional[str],
        slide_ocr: Optional[str],
        transcripts: List[str],
        timestamps: List[tuple[float, float]],
    ) -> Dict[str, Any]:
        """
        Generate a note section for a single slide + its linked transcripts.

        Returns a dict with title, content, key_concepts, summary.
        """
        combined_transcript = "\n\n".join(t.strip() for t in transcripts if t.strip())
        ts_start = timestamps[0][0] if timestamps else 0.0
        ts_end = timestamps[-1][1] if timestamps else 0.0

        prompt = SECTION_PROMPT_TEMPLATE.format(
            slide_title=slide_title or "(sin título)",
            slide_ocr=slide_ocr or "(sin texto OCR)",
            ts_start=ts_start,
            ts_end=ts_end,
            transcript=combined_transcript or "(sin transcripción)",
        )

        try:
            message = self._client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = message.content[0].text.strip()

            # Extract JSON from response (may be wrapped in ```json ... ```)
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            section_data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Claude JSON response: %s", exc)
            section_data = {
                "title": slide_title or "Sección sin título",
                "content": combined_transcript,
                "key_concepts": [],
                "summary": "",
            }
        except anthropic.APIError as exc:
            logger.error("Claude API error: %s", exc)
            section_data = {
                "title": slide_title or "Sección sin título",
                "content": f"[Error al generar notas: {exc}]",
                "key_concepts": [],
                "summary": "",
            }

        return section_data

    def build_full_note(
        self,
        document_title: str,
        sections_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Assemble the full note document from individual section data.

        Args:
            document_title: Title of the source document.
            sections_data: List of dicts produced by generate_section_note(),
                           each augmented with slide_number, timestamp_start,
                           timestamp_end, source_segments, source_frames.

        Returns:
            Complete note content dict ready for storage as JSONB.
        """
        return {
            "title": document_title,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sections": [
                {
                    "id": f"sec_{idx + 1}",
                    "title": sec.get("title", f"Sección {idx + 1}"),
                    "slide_number": sec.get("slide_number"),
                    "timestamp_start": sec.get("timestamp_start"),
                    "timestamp_end": sec.get("timestamp_end"),
                    "content": sec.get("content", ""),
                    "key_concepts": sec.get("key_concepts", []),
                    "summary": sec.get("summary", ""),
                    "source_segments": sec.get("source_segments", []),
                    "source_frames": sec.get("source_frames", []),
                }
                for idx, sec in enumerate(sections_data)
            ],
        }
