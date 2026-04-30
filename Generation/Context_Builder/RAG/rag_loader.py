"""
Loads all files from generation/RAG/ as LLM context.
- Gemini: PDFs → inline_data parts; JSON/MD → text parts
- Groq / text mode: PDFs extracted to Markdown text; JSON/MD → text blocks
Returns provider-specific structures consumed by prompt_builder.
"""
from __future__ import annotations

import base64
from pathlib import Path

from ...config import Config
from ..Parsing.pdf_extractor import extract_pdf_text


def load_rag(cfg: Config) -> tuple[list[dict], list[str]]:
    """
    Returns (gemini_parts, text_blocks).
    gemini_parts: list of Gemini 'parts' dicts (inline_data or text)
    text_blocks:  list of plain text strings (for Groq / system prompt injection)
    Both are populated; caller uses the appropriate one based on provider.
    """
    gemini_parts: list[dict] = []
    text_blocks:  list[str]  = []

    if not cfg.use_rag:
        print("  RAG disabled (use_rag=false in config)")
        return gemini_parts, text_blocks

    if not cfg.rag_dir.exists():
        print(f"  [MISSING] RAG folder not found: {cfg.rag_dir}")
        return gemini_parts, text_blocks

    for tmpl in sorted(cfg.rag_dir.iterdir()):
        if not tmpl.is_file():
            continue
        suffix   = tmpl.suffix.lower()
        size_kb  = tmpl.stat().st_size // 1024

        if suffix == ".pdf":
            if cfg.provider == "gemini":
                b64 = base64.b64encode(tmpl.read_bytes()).decode()
                gemini_parts.append({"inline_data": {"mime_type": "application/pdf", "data": b64}})
                gemini_parts.append({"text": f"[RAG] The above PDF is a reference document: {tmpl.name}"})
                print(f"  [OK] {tmpl.name}  (PDF, {size_kb} KB, inline_data)")
            else:
                txt = extract_pdf_text(tmpl, max_chars=None)
                text_blocks.append(f"[RAG] Reference document: {tmpl.name}\n\n{txt}")

        elif suffix == ".json":
            content = tmpl.read_text(encoding="utf-8")
            label   = f"[RAG] Reference JSON ({tmpl.name}):\n```json\n{content}\n```"
            gemini_parts.append({"text": label})
            text_blocks.append(label)
            print(f"  [OK] {tmpl.name}  (JSON, {size_kb} KB)")

        elif suffix == ".md":
            content = tmpl.read_text(encoding="utf-8")
            label   = f"[RAG] Reference document ({tmpl.name}):\n{content}"
            gemini_parts.append({"text": label})
            text_blocks.append(label)
            print(f"  [OK] {tmpl.name}  (Markdown, {size_kb} KB)")

        else:
            print(f"  [SKIP] {tmpl.name}  (unsupported type {suffix})")

    return gemini_parts, text_blocks
