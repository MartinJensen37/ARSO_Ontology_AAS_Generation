"""
PDF text and base64 extraction.
- Gemini: reads raw bytes → base64 (sent as inline_data)
- Claude / text mode: extracts Markdown text via pdfplumber (preserves tables)
"""
from __future__ import annotations

import base64
import re
import time
from pathlib import Path
from typing import Optional
from ...config import Config


def load_pdf(cfg: Config) -> tuple[Optional[str], Optional[str]]:
    """
    Returns (pdf_base64, pdf_text).
    Exactly one will be non-None (depending on provider), or both None if no PDF.
    """
    if cfg.pdf_path is None:
        print("  [SKIP] No PDF configured — text-only mode")
        return None, None

    pdf_path = cfg.pdf_path
    if not pdf_path.exists():
        import sys
        sys.exit(f"ERROR: PDF not found: {pdf_path}")

    if cfg.provider == "gemini":
        pdf_base64 = base64.b64encode(pdf_path.read_bytes()).decode()
        print(f"  [OK] {pdf_path.name}  ({pdf_path.stat().st_size // 1024} KB, sent as inline_data)")
        return pdf_base64, None
    else:
        return None, _extract_text(pdf_path, cfg.max_pdf_chars)


def extract_pdf_text(path: Path, max_chars: Optional[int] = None) -> str:
    """Public helper — extract Markdown text from any PDF file."""
    return _extract_text(path, max_chars)


def _table_to_md(table: list[list]) -> str:
    """Convert a pdfplumber table (list of rows) to a Markdown table string."""
    if not table or not table[0]:
        return ""
    def cell(v: object) -> str:
        return re.sub(r"\s+", " ", str(v or "").strip())
    header = table[0]
    rows = table[1:]
    lines = [
        "| " + " | ".join(cell(c) for c in header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell(c) for c in row) + " |")
    return "\n".join(lines)


def _extract_text(pdf_path: Path, max_chars: Optional[int]) -> str:
    print(f"  Extracting text from {pdf_path.name}... ", end="", flush=True)
    t0 = time.time()
    try:
        import pdfplumber
        chunks: list[str] = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                # Bounding boxes of detected tables — used to crop them out of text
                table_bboxes = [t.bbox for t in page.find_tables()]

                # Extract text from the region outside table bounding boxes
                if table_bboxes:
                    remaining = page
                    for bbox in table_bboxes:
                        remaining = remaining.outside_bbox(bbox)
                    prose = remaining.extract_text() or ""
                else:
                    prose = page.extract_text() or ""

                if prose.strip():
                    chunks.append(prose.strip())

                for table in tables:
                    md = _table_to_md(table)
                    if md:
                        chunks.append(md)

        text = "\n\n".join(chunks)
    except Exception as exc:
        print(f"pdfplumber failed ({exc}), falling back to fitz... ", end="", flush=True)
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
    if max_chars and len(text) > max_chars:
        text = text[:max_chars]
        print(f"done in {time.time()-t0:.1f}s  (truncated to {max_chars:,} chars)")
    else:
        print(f"done in {time.time()-t0:.1f}s  ({len(text):,} chars)")
    return text
