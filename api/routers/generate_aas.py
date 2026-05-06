"""
POST /api/generate-aas  - SSE streaming AAS generation via Generation pipeline.
GET  /api/generation-config - available providers and model lists (no API keys).

The endpoint accepts all generation options from the UI. API keys are always
read from Generation/config.yaml and are never exposed to the client.
"""
from __future__ import annotations

import asyncio
import base64
import concurrent.futures
import json
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from Generation.config import Config, load_config
from Generation.Context_Builder.context_loader import load_context
from Generation.Context_Builder.RAG.rag_loader import load_rag
from Generation.Context_Builder.RAG.prompt_builder import build_system_instruction, build_user_prompt
from Generation.pipeline import run_pipeline

router = APIRouter()


class SupplementalFile(BaseModel):
    file_name: str
    mime_type: Optional[str] = None
    content_base64: str


class GenerateAasRequest(BaseModel):
    asset_name: str = "UnknownAsset"
    base_url: str = "https://smartproductionlab.aau.dk"
    selected_submodels: list[str] = ["Nameplate", "HierarchicalStructures"]

    spec_sheet_text: str = ""
    spec_sheet_pdf_base64: Optional[str] = None
    spec_sheet_pdf_mime_type: str = "application/pdf"
    supplemental_files: list[SupplementalFile] = Field(default_factory=list)

    provider: str = "gemini"
    model: Optional[str] = None

    generation_mode: str = "json-description"
    use_rag: bool = False
    use_example: bool = False
    force_full_aas_output: bool = True
    max_pdf_chars: Optional[int] = 8000
    max_attempts: int = 2


class GenerationConfigResponse(BaseModel):
    providers: list[str]
    models: dict[str, list[str]]
    defaults: dict


def _extract_xml_opcua_summary(xml_text: str, file_name: str) -> str:
    """Extract a compact OPC UA NodeSet summary for submodel population hints."""

    def _local(tag: str) -> str:
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag

    try:
        root = ET.fromstring(xml_text)
    except Exception as exc:
        return f"[File: {file_name}] OPC UA XML parse failed: {exc}"

    tag_name = _local(root.tag)
    if tag_name.lower() != "uanodeset" and "opcfoundation.org/UA" not in root.tag:
        return ""

    namespace_uris: list[str] = []
    models: list[str] = []
    variables: list[str] = []
    methods: list[str] = []
    objects: list[str] = []
    endpoint_hits: list[str] = []

    for elem in root.iter():
        local = _local(elem.tag)

        if local == "Uri" and elem.text and elem.text.strip():
            namespace_uris.append(elem.text.strip())

        if local == "Model":
            model_uri = elem.attrib.get("ModelUri")
            if model_uri:
                models.append(model_uri)

        browse_name = elem.attrib.get("BrowseName", "")
        node_id = elem.attrib.get("NodeId", "")

        if local == "UAVariable":
            dtype = elem.attrib.get("DataType", "")
            desc = browse_name or node_id or "(unnamed variable)"
            if dtype:
                desc = f"{desc} [{dtype}]"
            variables.append(desc)
        elif local == "UAMethod":
            methods.append(browse_name or node_id or "(unnamed method)")
        elif local == "UAObject":
            objects.append(browse_name or node_id or "(unnamed object)")

        if local in {"EndpointUrl", "DiscoveryUrl", "Url", "Address", "Endpoint", "ServerUri"}:
            text_val = (elem.text or "").strip()
            if text_val:
                endpoint_hits.append(text_val)

        if not endpoint_hits and elem.text:
            text_val = elem.text.strip()
            if text_val and re.search(r"(opc\.tcp://|https?://|\bIP\b|\bAddress\b)", text_val, flags=re.IGNORECASE):
                endpoint_hits.append(text_val)

    object_skill_candidates = [
        o for o in objects
        if re.search(r"(skill|operation|command|capability)", o, flags=re.IGNORECASE)
    ]
    skill_candidates = list(dict.fromkeys([*methods, *object_skill_candidates]))

    def _head(items: list[str], n: int = 20) -> str:
        if not items:
            return "none"
        uniq = list(dict.fromkeys(items))
        shown = uniq[:n]
        tail = f" (+{len(uniq) - n} more)" if len(uniq) > n else ""
        return "; ".join(shown) + tail

    summary_lines = [
        f"[File: {file_name}] OPC UA NodeSet summary:",
        f"- Namespaces: {_head(namespace_uris, 8)}",
        f"- Models: {_head(models, 8)}",
        f"- Variables ({len(variables)}): {_head(variables, 25)}",
        f"- Methods ({len(methods)}): {_head(methods, 25)}",
        f"- Skill candidates ({len(skill_candidates)}): {_head(skill_candidates, 25)}",
        f"- Endpoint/address hints: {_head(endpoint_hits, 15)}",
        "- Mapping guidance: map methods/skill candidates to Skills, variables to Variables, and endpoint/address hints to AssetInterfacesDescription (AID) when those submodels are selected.",
    ]
    return "\n".join(summary_lines)


def _decode_text_bytes(data: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")


def _extract_file_context(
    uploaded: SupplementalFile,
    provider: str,
    max_chars: Optional[int],
) -> tuple[str, Optional[str]]:
    """Return (text_context, pdf_base64_for_gemini)."""
    file_name = uploaded.file_name
    mime = (uploaded.mime_type or "").lower()
    suffix = Path(file_name).suffix.lower()

    raw = base64.b64decode(uploaded.content_base64)

    if mime == "application/pdf" or suffix == ".pdf":
        if provider == "gemini":
            return f"[File: {file_name}] PDF attached as binary context for Gemini.", uploaded.content_base64
        try:
            import pymupdf4llm  # type: ignore

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(raw)
                tmp_pdf = Path(f.name)
            text = pymupdf4llm.to_markdown(str(tmp_pdf))
            tmp_pdf.unlink(missing_ok=True)
            if max_chars:
                text = text[:max_chars]
            return f"[File: {file_name}] PDF extracted text:\n{text}", None
        except Exception as exc:
            return f"[File: {file_name}] PDF extraction failed: {exc}", None

    text = _decode_text_bytes(raw)
    if max_chars:
        text = text[:max_chars]

    if suffix in {".xml", ".nodeset", ".nodeset2"} or "xml" in mime:
        opcua_summary = _extract_xml_opcua_summary(text, file_name)
        if opcua_summary:
            return opcua_summary + "\n\nRaw excerpt:\n" + text[:6000], None

    return f"[File: {file_name}]\n{text}", None


@router.get("/generation-config", response_model=GenerationConfigResponse)
async def get_generation_config() -> GenerationConfigResponse:
    """Return providers and model lists from config.yaml (no API keys)."""
    try:
        cfg = load_config()
        return GenerationConfigResponse(
            providers=["gemini", "groq", "claude"],
            models={
                "gemini": cfg.gemini_models,
                "groq": cfg.groq_models,
                "claude": cfg.claude_models,
            },
            defaults={
                "provider": cfg.provider,
                "generation_mode": "json-description",
                "use_rag": cfg.use_rag,
                "use_example": cfg.use_example,
                "force_full_aas_output": cfg.force_full_aas_output,
                "max_pdf_chars": cfg.max_pdf_chars,
                "max_attempts": cfg.max_attempts,
            },
        )
    except Exception:
        return GenerationConfigResponse(
            providers=["gemini", "groq", "claude"],
            models={"gemini": [], "groq": [], "claude": []},
            defaults={},
        )


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


async def _stream_pipeline(req: GenerateAasRequest) -> AsyncGenerator[str, None]:
    """Run the generation pipeline in a thread and yield SSE events."""

    try:
        base_cfg = load_config()
    except SystemExit as exc:
        yield _sse({"type": "error", "message": f"Config load error: {exc}"})
        return
    except Exception as exc:
        yield _sse({"type": "error", "message": f"Config load error: {exc}"})
        return

    if req.provider == "gemini":
        api_key = base_cfg.gemini_api_key
    elif req.provider == "groq":
        api_key = base_cfg.groq_api_key
    elif req.provider == "claude":
        api_key = base_cfg.claude_api_key
    else:
        yield _sse({"type": "error", "message": f"Unsupported provider '{req.provider}'"})
        return

    if req.provider in {"gemini", "groq"} and not api_key:
        yield _sse({
            "type": "error",
            "message": (
                f"No API key configured for provider '{req.provider}' in "
                "Generation/config.yaml"
            ),
        })
        return

    if req.provider == "gemini":
        base_models = base_cfg.gemini_models
    elif req.provider == "groq":
        base_models = base_cfg.groq_models
    else:
        base_models = base_cfg.claude_models

    if req.model:
        model_list = [req.model, *[m for m in base_models if m != req.model]]
    else:
        model_list = base_models

    cfg = Config(
        provider=req.provider,
        api_key=api_key,
        asset_name=req.asset_name,
        base_url=req.base_url,
        pdf_path=None,
        submodels=req.selected_submodels,
        generation_mode=req.generation_mode,
        profile_example_path=base_cfg.profile_example_path,
        use_rag=req.use_rag,
        use_example=req.use_example,
        force_full_aas_output=req.force_full_aas_output,
        max_pdf_chars=req.max_pdf_chars,
        max_attempts=req.max_attempts,
        models=model_list,
        gemini_models=base_cfg.gemini_models,
        groq_models=base_cfg.groq_models,
        claude_models=base_cfg.claude_models,
        gemini_api_key=base_cfg.gemini_api_key,
        groq_api_key=base_cfg.groq_api_key,
        claude_api_key=base_cfg.claude_api_key,
        gen_dir=base_cfg.gen_dir,
        root_dir=base_cfg.root_dir,
        context_dir=base_cfg.context_dir,
        rag_dir=base_cfg.rag_dir,
        output_json=base_cfg.output_json,
        output_issues=base_cfg.output_issues,
        shacl_shapes=base_cfg.shacl_shapes,
        ontology_paths=base_cfg.ontology_paths,
    )

    yield _sse({
        "type": "log",
        "message": (
            f"Starting generation - provider: {req.provider} | "
            f"mode: {req.generation_mode} | "
            f"model: {model_list[0] if model_list else '(default)'} | "
            f"max_attempts: {req.max_attempts}"
        ),
    })

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[dict] = asyncio.Queue()

    _ATTEMPT_RE = re.compile(r"--\s+Attempt\s+(\d+)/(\d+)")
    _RESPONSE_RE = re.compile(r"Response:\s+[\d,]+\s+chars")

    def progress_callback(msg: str) -> None:
        stripped = msg.strip()
        if not stripped:
            return
        asyncio.run_coroutine_threadsafe(
            queue.put({"type": "log", "message": stripped}), loop
        )
        m = _ATTEMPT_RE.search(stripped)
        if m:
            asyncio.run_coroutine_threadsafe(
                queue.put({
                    "type": "stage",
                    "stage": "querying",
                    "attempt": int(m.group(1)),
                    "max_attempts": int(m.group(2)),
                }),
                loop,
            )
        elif _RESPONSE_RE.search(stripped):
            asyncio.run_coroutine_threadsafe(
                queue.put({
                    "type": "stage",
                    "stage": "validating",
                    "attempt": 0,
                    "max_attempts": cfg.max_attempts,
                }),
                loop,
            )

    def _run_in_thread() -> None:
        try:
            asyncio.run_coroutine_threadsafe(
                queue.put({
                    "type": "stage",
                    "stage": "preparing",
                    "attempt": 0,
                    "max_attempts": cfg.max_attempts,
                }),
                loop,
            )

            context_text = load_context(cfg)

            rag_gemini_parts: list[dict] = []
            rag_text_blocks: list[str] = []
            if cfg.use_rag:
                rag_gemini_parts, rag_text_blocks = load_rag(cfg)

            system_instruction = build_system_instruction(cfg, context_text, rag_text_blocks)

            incoming_files = list(req.supplemental_files)
            if req.spec_sheet_pdf_base64:
                incoming_files.append(
                    SupplementalFile(
                        file_name="spec-sheet.pdf",
                        mime_type=req.spec_sheet_pdf_mime_type or "application/pdf",
                        content_base64=req.spec_sheet_pdf_base64,
                    )
                )

            spec_text_blocks: list[str] = []

            pdf_base64: Optional[str] = None
            pdf_text: Optional[str] = None

            if incoming_files:
                asyncio.run_coroutine_threadsafe(
                    queue.put({
                        "type": "log",
                        "message": f"Processing {len(incoming_files)} supplemental file(s)...",
                    }),
                    loop,
                )

            for uploaded in incoming_files:
                try:
                    text_context, gemini_pdf = _extract_file_context(uploaded, req.provider, req.max_pdf_chars)
                except Exception as exc:
                    text_context = f"[File: {uploaded.file_name}] processing failed: {exc}"
                    gemini_pdf = None

                if text_context:
                    spec_text_blocks.append(text_context)
                if gemini_pdf and not pdf_base64:
                    pdf_base64 = gemini_pdf
                elif gemini_pdf and pdf_base64:
                    spec_text_blocks.append(
                        f"[File: {uploaded.file_name}] Additional PDF detected. Only one inline PDF can be attached for Gemini; use extracted text or summary from other files."
                    )

            supplemental_context: Optional[str] = None
            if spec_text_blocks:
                combined = "\n\n---\n\n".join(spec_text_blocks)
                if req.provider != "gemini" and req.max_pdf_chars:
                    combined = combined[: max(2000, req.max_pdf_chars * 3)]
                supplemental_context = combined
                if req.provider != "gemini":
                    pdf_text = combined

            user_prompt = build_user_prompt(
                cfg,
                pdf_base64,
                pdf_text,
                spec_sheet_text=req.spec_sheet_text,
                supplemental_context=supplemental_context,
            )

            aas_json, conforms, issues, attempts, _attempts_debug = run_pipeline(
                cfg,
                system_instruction,
                user_prompt,
                pdf_base64,
                rag_gemini_parts,
                progress_callback=progress_callback,
            )

            asyncio.run_coroutine_threadsafe(
                queue.put({
                    "type": "result",
                    "conforms": conforms,
                    "aas_json": aas_json,
                    "attempts": attempts,
                    "issues": issues,
                }),
                loop,
            )
        except BaseException as exc:
            asyncio.run_coroutine_threadsafe(
                queue.put({"type": "error", "message": str(exc)}),
                loop,
            )

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = loop.run_in_executor(executor, _run_in_thread)

    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=0.3)
            yield _sse(event)
            if event.get("type") in ("result", "error"):
                break
        except asyncio.TimeoutError:
            if future.done():
                while not queue.empty():
                    event = queue.get_nowait()
                    yield _sse(event)
                    if event.get("type") in ("result", "error"):
                        return
                yield _sse({
                    "type": "error",
                    "message": "Pipeline completed without returning a result.",
                })
                return
        except Exception as exc:
            yield _sse({"type": "error", "message": str(exc)})
            break


@router.post("/generate-aas")
async def generate_aas(req: GenerateAasRequest) -> StreamingResponse:
    return StreamingResponse(
        _stream_pipeline(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
