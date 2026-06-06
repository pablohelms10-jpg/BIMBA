from __future__ import annotations

import io
import logging
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


async def export_note(
    content: Dict[str, Any],
    format: str,
    document_id: str,
) -> Tuple[bytes, str, str]:
    """
    Export a note content dict to the requested format.

    Returns:
        (bytes_content, media_type, filename)
    """
    if format == "md":
        return _export_markdown(content, document_id)
    elif format == "txt":
        return _export_txt(content, document_id)
    elif format == "pdf":
        return _export_pdf(content, document_id)
    elif format == "docx":
        return _export_docx(content, document_id)
    else:
        raise ValueError(f"Unsupported export format: {format}")


def _safe_title(content: Dict[str, Any]) -> str:
    return content.get("title", "Notas BIMBA")


def _export_markdown(content: Dict[str, Any], document_id: str) -> Tuple[bytes, str, str]:
    """Export notes as Markdown."""
    lines = [f"# {_safe_title(content)}\n"]
    generated_at = content.get("generated_at", "")
    if generated_at:
        lines.append(f"*Generado: {generated_at}*\n")
    lines.append("")

    for section in content.get("sections", []):
        title = section.get("title", "Sección")
        slide_num = section.get("slide_number")
        ts_start = section.get("timestamp_start")
        ts_end = section.get("timestamp_end")

        meta_parts = []
        if slide_num:
            meta_parts.append(f"Slide {slide_num}")
        if ts_start is not None and ts_end is not None:
            meta_parts.append(f"{_fmt_time(ts_start)} – {_fmt_time(ts_end)}")

        lines.append(f"## {title}")
        if meta_parts:
            lines.append(f"*{' | '.join(meta_parts)}*\n")

        body = section.get("content", "")
        if body:
            lines.append(body)
            lines.append("")

        concepts = section.get("key_concepts", [])
        if concepts:
            lines.append("**Conceptos clave:** " + ", ".join(concepts))
            lines.append("")

        summary = section.get("summary", "")
        if summary:
            lines.append(f"> **Resumen:** {summary}")
            lines.append("")

    md_text = "\n".join(lines)
    filename = f"bimba_notes_{document_id[:8]}.md"
    return md_text.encode("utf-8"), "text/markdown; charset=utf-8", filename


def _export_txt(content: Dict[str, Any], document_id: str) -> Tuple[bytes, str, str]:
    """Export notes as plain text."""
    lines = [_safe_title(content), "=" * 60, ""]
    for section in content.get("sections", []):
        lines.append(f"[{section.get('title', 'Sección')}]")
        body = section.get("content", "")
        if body:
            # Strip markdown formatting for plain text
            import re
            clean = re.sub(r"[#*_`>]", "", body)
            lines.append(clean.strip())
        concepts = section.get("key_concepts", [])
        if concepts:
            lines.append("Conceptos clave: " + ", ".join(concepts))
        lines.append("")

    txt = "\n".join(lines)
    filename = f"bimba_notes_{document_id[:8]}.txt"
    return txt.encode("utf-8"), "text/plain; charset=utf-8", filename


def _export_pdf(content: Dict[str, Any], document_id: str) -> Tuple[bytes, str, str]:
    """Export notes as PDF using reportlab."""
    from reportlab.lib import colors  # type: ignore
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (  # type: ignore
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        HRFlowable,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "BimbaTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=12,
        textColor=colors.HexColor("#1a1a2e"),
    )
    h2_style = ParagraphStyle(
        "BimbaH2",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=4,
        textColor=colors.HexColor("#16213e"),
    )
    body_style = ParagraphStyle(
        "BimbaBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "BimbaMeta",
        parent=styles["Italic"],
        fontSize=9,
        textColor=colors.gray,
        spaceAfter=6,
    )
    concept_style = ParagraphStyle(
        "BimbaConceptos",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#0f3460"),
        spaceAfter=8,
    )

    story.append(Paragraph(_safe_title(content), title_style))
    generated_at = content.get("generated_at", "")
    if generated_at:
        story.append(Paragraph(f"Generado: {generated_at}", meta_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey, spaceAfter=12))

    for section in content.get("sections", []):
        title = section.get("title", "Sección")
        slide_num = section.get("slide_number")
        ts_start = section.get("timestamp_start")
        ts_end = section.get("timestamp_end")

        story.append(Paragraph(title, h2_style))

        meta_parts = []
        if slide_num:
            meta_parts.append(f"Slide {slide_num}")
        if ts_start is not None and ts_end is not None:
            meta_parts.append(f"{_fmt_time(ts_start)} – {_fmt_time(ts_end)}")
        if meta_parts:
            story.append(Paragraph(" | ".join(meta_parts), meta_style))

        body = section.get("content", "")
        if body:
            import re
            # Basic markdown→plain conversion for reportlab
            clean = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", body)
            clean = re.sub(r"\*(.+?)\*", r"<i>\1</i>", clean)
            clean = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", clean)
            for line in clean.split("\n"):
                line = line.strip()
                if line.startswith("# "):
                    story.append(Paragraph(line[2:], h2_style))
                elif line.startswith("## "):
                    story.append(Paragraph(line[3:], h2_style))
                elif line.startswith("> "):
                    story.append(Paragraph(f"<i>{line[2:]}</i>", meta_style))
                elif line:
                    try:
                        story.append(Paragraph(line, body_style))
                    except Exception:
                        story.append(Paragraph(line.replace("<", "&lt;").replace(">", "&gt;"), body_style))

        concepts = section.get("key_concepts", [])
        if concepts:
            story.append(
                Paragraph(
                    "<b>Conceptos clave:</b> " + ", ".join(concepts),
                    concept_style,
                )
            )

        summary = section.get("summary", "")
        if summary:
            story.append(Paragraph(f"<i>Resumen: {summary}</i>", meta_style))

        story.append(Spacer(1, 8))

    doc.build(story)
    buffer.seek(0)
    filename = f"bimba_notes_{document_id[:8]}.pdf"
    return buffer.read(), "application/pdf", filename


def _export_docx(content: Dict[str, Any], document_id: str) -> Tuple[bytes, str, str]:
    """Export notes as DOCX using python-docx."""
    from docx import Document as DocxDocument  # type: ignore
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = DocxDocument()

    # Title
    title_para = doc.add_heading(_safe_title(content), level=0)

    generated_at = content.get("generated_at", "")
    if generated_at:
        p = doc.add_paragraph(f"Generado: {generated_at}")
        p.runs[0].font.italic = True
        p.runs[0].font.size = Pt(9)
        p.runs[0].font.color.rgb = RGBColor(0x88, 0x88, 0x88)

    doc.add_paragraph()  # spacer

    for section in content.get("sections", []):
        title = section.get("title", "Sección")
        slide_num = section.get("slide_number")
        ts_start = section.get("timestamp_start")
        ts_end = section.get("timestamp_end")

        doc.add_heading(title, level=2)

        meta_parts = []
        if slide_num:
            meta_parts.append(f"Slide {slide_num}")
        if ts_start is not None and ts_end is not None:
            meta_parts.append(f"{_fmt_time(ts_start)} – {_fmt_time(ts_end)}")
        if meta_parts:
            p = doc.add_paragraph(" | ".join(meta_parts))
            p.runs[0].font.italic = True
            p.runs[0].font.size = Pt(9)
            p.runs[0].font.color.rgb = RGBColor(0x88, 0x88, 0x88)

        body = section.get("content", "")
        if body:
            import re
            # Strip markdown decorators for plain docx paragraphs
            clean_body = re.sub(r"[#*_`>]", "", body).strip()
            for line in clean_body.split("\n"):
                line = line.strip()
                if line:
                    doc.add_paragraph(line)

        concepts = section.get("key_concepts", [])
        if concepts:
            p = doc.add_paragraph()
            run = p.add_run("Conceptos clave: ")
            run.bold = True
            p.add_run(", ".join(concepts))

        summary = section.get("summary", "")
        if summary:
            p = doc.add_paragraph(f"Resumen: {summary}")
            p.runs[0].font.italic = True

        doc.add_paragraph()  # section spacer

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    filename = f"bimba_notes_{document_id[:8]}.docx"
    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return buffer.read(), mime, filename


def _fmt_time(seconds: float) -> str:
    """Format seconds as MM:SS."""
    secs = int(seconds)
    return f"{secs // 60:02d}:{secs % 60:02d}"
