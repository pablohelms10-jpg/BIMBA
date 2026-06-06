from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    full_text: str
    title: Optional[str]          # Inferred largest-font line
    body: str
    page_number: Optional[int] = None


class OCRService:
    """OCR extraction using pytesseract and pdfplumber."""

    def ocr_image(self, image_path: str) -> OCRResult:
        """
        Run Tesseract OCR on a single image.
        Infers slide title from the first non-empty line.
        """
        import pytesseract  # type: ignore
        from PIL import Image

        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang="spa+eng", config="--psm 3")
            img.close()
        except Exception as exc:
            logger.error("OCR failed for %s: %s", image_path, exc)
            return OCRResult(full_text="", title=None, body="")

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        title = lines[0] if lines else None
        body = "\n".join(lines[1:]) if len(lines) > 1 else ""

        return OCRResult(full_text=text.strip(), title=title, body=body)

    def extract_pdf_text(self, pdf_path: str) -> List[OCRResult]:
        """
        Extract text from a PDF using pdfplumber (native text layer).
        Falls back to image-based OCR for pages without native text.
        """
        import pdfplumber  # type: ignore

        results: List[OCRResult] = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    native_text = page.extract_text() or ""
                    native_text = native_text.strip()

                    if native_text:
                        lines = [l.strip() for l in native_text.splitlines() if l.strip()]
                        title = lines[0] if lines else None
                        body = "\n".join(lines[1:]) if len(lines) > 1 else ""
                        results.append(
                            OCRResult(
                                full_text=native_text,
                                title=title,
                                body=body,
                                page_number=page_num,
                            )
                        )
                    else:
                        # No native text — convert page to image and OCR
                        page_image = page.to_image(resolution=150)
                        with _temp_png(page_image) as tmp_path:
                            ocr_result = self.ocr_image(tmp_path)
                        ocr_result.page_number = page_num
                        results.append(ocr_result)
        except Exception as exc:
            logger.error("pdfplumber failed for %s: %s", pdf_path, exc)

        return results

    def convert_pdf_to_images(self, pdf_path: str, output_dir: str) -> List[str]:
        """
        Convert each PDF page to a JPEG image using pdf2image.
        Returns list of image paths.
        """
        from pdf2image import convert_from_path  # type: ignore

        os.makedirs(output_dir, exist_ok=True)
        images = convert_from_path(pdf_path, dpi=150)
        paths: List[str] = []
        for idx, img in enumerate(images, start=1):
            dest = os.path.join(output_dir, f"page_{idx:04d}.jpg")
            img.save(dest, "JPEG")
            paths.append(dest)
        return paths


import contextlib
import tempfile


@contextlib.contextmanager
def _temp_png(page_image):
    """Context manager: save a pdfplumber PageImage to a temp file, yield path."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name
    try:
        page_image.save(tmp_path)
        yield tmp_path
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
