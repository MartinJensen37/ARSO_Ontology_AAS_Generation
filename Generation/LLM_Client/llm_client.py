"""Provider-agnostic LLM client for the generation pipeline.

Supports any OpenAI-compatible chat-completions endpoint (see
OPENAI_COMPATIBLE_BASE_URLS), Gemini via the Google GenAI SDK (native PDF
input), and the Claude Code CLI via `claude -p`. Handles model-cycling on rate
limits and provider-specific response parsing behind one interface.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from uuid import uuid4
from typing import Any
from typing import Optional


REQUEST_TIMEOUT_SECONDS = 600
OPENAI_COMPATIBLE_MIN_OUTPUT_TOKENS = 256
OPENAI_COMPATIBLE_MAX_OUTPUT_TOKENS = 2048
DEBUG_IO_ENV = "GEN_DEBUG_IO"

# Providers with a hard per-minute *token* budget, needing max_tokens shrunk
# ahead of the request. Only add a provider here with a known TPM figure -- too
# small a budget silently yields empty content instead of an error.
_OPENAI_COMPATIBLE_TPM_SAFETY_BUDGET: dict[str, int] = {
    "groq": 7000,
}

# Every OpenAI-compatible provider, keyed by the `provider` name in config.yaml.
# Adding one needs only a base_url here plus api_keys/models in config.yaml.
OPENAI_COMPATIBLE_BASE_URLS: dict[str, str] = {
    "groq":       "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "deepseek":   "https://api.deepseek.com",
}

# Optional extra headers per OpenAI-compatible provider (e.g. OpenRouter uses
# these for attribution / its model-ranking leaderboard; harmless to omit).
_OPENAI_COMPATIBLE_EXTRA_HEADERS: dict[str, dict[str, str]] = {
    "openrouter": {
        "HTTP-Referer": "https://smartproductionlab.aau.dk",
        "X-Title": "ARSO AAS Generator",
    },
}

try:
    from google import genai  # type: ignore[import-not-found]
except Exception:
    genai = None

try:
    from openai import OpenAI  # type: ignore[import-not-found]
except Exception:
    OpenAI = None

def _is_rate_limit_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code == 429:
        return True

    code = getattr(exc, "code", None)
    if code == 429:
        return True

    message = str(exc).lower()
    return "429" in message or "rate limit" in message or "quota" in message


def _is_switchable_model_error(exc: Exception) -> bool:
    if isinstance(exc, TimeoutError):
        return True

    if _is_rate_limit_error(exc):
        return True

    status_code = getattr(exc, "status_code", None)
    code = getattr(exc, "code", None)
    message = str(exc).lower()

    if status_code == 413 or code == 413:
        return True

    token_limit_markers = [
        "request too large",
        "tokens per minute",
        "requested",
        "rate_limit_exceeded",
    ]
    if any(marker in message for marker in token_limit_markers):
        return True

    decommission_markers = [
        "decommissioned",
        "no longer supported",
        "model_decommissioned",
    ]
    if any(marker in message for marker in decommission_markers):
        return True

    return False


def _error_details(exc: Exception) -> tuple[str | None, str | None, str]:
    if isinstance(exc, TimeoutError):
        return None, "timeout", str(exc)

    status_code = getattr(exc, "status_code", None)
    code = getattr(exc, "code", None)

    message_text = str(exc)
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            code = code or err.get("code")
            message_text = str(err.get("message") or message_text)

    return (
        str(status_code) if status_code is not None else None,
        str(code) if code is not None else None,
        message_text,
    )


def _error_category(exc: Exception) -> str:
    if isinstance(exc, TimeoutError):
        return "error"

    message = str(exc).lower()
    if _is_rate_limit_error(exc) or "request too large" in message or "tokens per minute" in message:
        return "limit"
    return "error"


def _invoke_with_timeout(callable_fn, timeout_seconds: int) -> Any:
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(callable_fn)
        try:
            return future.result(timeout=timeout_seconds)
        except FutureTimeoutError as exc:
            raise TimeoutError(f"Request timed out after {timeout_seconds}s") from exc


def _extract_gemini_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if text:
        return str(text)

    try:
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            content = getattr(candidates[0], "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                part_text = getattr(part, "text", None)
                if part_text:
                    return str(part_text)
    except Exception:
        pass

    return ""


def _estimate_text_tokens(text: str) -> int:
    # Coarse estimate good enough for pre-flight token budgeting.
    return max(1, len(text) // 4)


def _resolve_openai_compatible_max_tokens(
    provider: str, system_instruction: str, history: Optional[list[dict]]
) -> Optional[int]:
    """Return a max_tokens value to send, or None to send no cap at all.

    Only providers in _OPENAI_COMPATIBLE_TPM_SAFETY_BUDGET (an external,
    hard per-minute rate limit) get a computed cap here. Everyone else gets
    None -- no self-imposed ceiling -- so a reasoning model's chain-of-thought
    always has room to finish before the answer, however long that takes.
    """
    budget = _OPENAI_COMPATIBLE_TPM_SAFETY_BUDGET.get(provider)
    if budget is None:
        return None

    payload_text = system_instruction
    for msg in history or []:
        content = msg.get("content") if isinstance(msg, dict) else ""
        if isinstance(content, str):
            payload_text += "\n" + content

    estimated_input = _estimate_text_tokens(payload_text)
    available = budget - estimated_input
    bounded = min(OPENAI_COMPATIBLE_MAX_OUTPUT_TOKENS, max(OPENAI_COMPATIBLE_MIN_OUTPUT_TOKENS, available))
    return bounded


def _extract_claude_json_payload(stdout_text: str) -> dict[str, Any]:
    text = stdout_text.strip()
    if not text:
        raise RuntimeError("Claude CLI returned empty stdout")

    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass

    # Fallback: parse line-delimited JSON and pick the last object.
    last_obj: dict[str, Any] | None = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            candidate = json.loads(line)
        except Exception:
            continue
        if isinstance(candidate, dict):
            last_obj = candidate
    if last_obj is None:
        raise RuntimeError("Could not parse JSON payload from Claude CLI output")
    return last_obj


def _debug_enabled() -> bool:
    value = os.getenv(DEBUG_IO_ENV, "0").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _debug_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _debug_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _prepare_debug_paths(provider: str, model_name: str) -> dict[str, Path]:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    token = uuid4().hex[:8]
    safe_model = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in model_name)
    base = Path.cwd() / "generation" / "output" / "debug_io"
    prefix = f"{stamp}-{provider}-{safe_model}-{token}"
    return {
        "system": base / f"{prefix}.system.txt",
        "conversation": base / f"{prefix}.conversation.txt",
        "request": base / f"{prefix}.request.json",
        "response": base / f"{prefix}.response.txt",
        "meta": base / f"{prefix}.meta.txt",
    }


def _run_claude_cli(
    *,
    model_name: str,
    system_instruction: str,
    conversation_text: str,
    max_output_tokens: Optional[int] = None,
) -> tuple[str, bool]:
    """Invoke the Claude Code CLI in print mode.

    Sends the conversation via stdin rather than a file, so the CLI needs no
    tool use and cannot emit duplicate tool_use blocks.

    Args:
        model_name: Model id passed to `claude --model`.
        system_instruction: Appended via --append-system-prompt-file.
        conversation_text: Prompt piped to the CLI on stdin.
        max_output_tokens: Optional output cap; uncapped if None.

    Returns:
        (response_text, rate_limited)
    """
    with tempfile.TemporaryDirectory(prefix="claude-llm-client-") as tmp:
        tmp_dir = Path(tmp)
        system_file = tmp_dir / "system_instruction.txt"
        system_file.write_text(system_instruction, encoding="utf-8")

        # The conversation goes via stdin (see _run below); -p with no arg
        # tells the CLI to read the prompt from stdin.
        def _build_cmd(
            include_bare: bool,
            include_max_tokens: bool,
            include_system_file: bool,
        ) -> list[str]:
            cmd = ["claude"]
            if include_bare:
                cmd.append("--bare")
            cmd.extend([
                "-p",
                "--output-format",
                "json",
                "--model",
                model_name,
            ])
            if include_system_file:
                cmd.extend(["--append-system-prompt-file", str(system_file)])
            if include_max_tokens and max_output_tokens is not None:
                cmd.extend(["--max-output-tokens", str(max_output_tokens)])
            return cmd

        include_bare = True
        include_max_tokens = max_output_tokens is not None
        include_system_file = True
        proc = None

        for _ in range(4):
            cmd = _build_cmd(include_bare, include_max_tokens, include_system_file)
            proc = subprocess.run(
                cmd,
                cwd=str(Path.cwd()),
                env=os.environ.copy(),
                input=conversation_text,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            if proc.returncode == 0:
                break

            merged = ((proc.stderr or "") + "\n" + (proc.stdout or "")).lower()
            if include_bare and "unknown option '--bare'" in merged:
                include_bare = False
                continue
            if include_max_tokens and "unknown option '--max-output-tokens'" in merged:
                include_max_tokens = False
                continue
            if include_system_file and "unknown option '--append-system-prompt-file'" in merged:
                include_system_file = False
                continue
            break

        if proc is None:
            raise RuntimeError("Claude CLI process did not start")
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip() or "Unknown Claude CLI error"
            raise RuntimeError(detail)

        payload = _extract_claude_json_payload(proc.stdout)
        # Detect API errors that the CLI surfaces inside its result envelope
        # (returncode 0 but is_error=true). Treat the same as a non-zero exit.
        if isinstance(payload, dict) and payload.get("is_error"):
            detail = str(payload.get("result") or payload).strip() or "Unknown Claude CLI error"
            raise RuntimeError(detail)

        result_text = str(payload.get("result") or "").strip()
        if not result_text:
            raise RuntimeError("Claude CLI output JSON did not contain a non-empty 'result' field")
        return result_text, include_max_tokens


def call_llm(
    provider: str,
    api_key: str,
    models: list[str],
    model_idx: int,
    system_instruction: str,
    gemini_contents: Optional[list[dict]] = None,
    groq_history: Optional[list[dict]] = None,
    generation_mode: str = "json",
) -> tuple[str, int]:
    """
    Make one LLM call. Returns (raw_text, model_idx).
    model_idx may change if a 429 caused a model switch.
    Calls sys.exit() if all models are exhausted on 429.
    """
    if not models:
        sys.exit(f"\n[STOP] No models configured for provider '{provider}'.")

    model_name = models[model_idx]
    debug_paths: dict[str, Path] | None = _prepare_debug_paths(provider, model_name) if _debug_enabled() else None

    if provider == "gemini":
        output_tokens = None
        body_preview = {
            "system_instruction": system_instruction,
            "contents": gemini_contents,
            "generationConfig": {"temperature": 0.1},
        }
    elif provider in OPENAI_COMPATIBLE_BASE_URLS:
        output_tokens = _resolve_openai_compatible_max_tokens(provider, system_instruction, groq_history)
        body_preview = {
            "model": model_name,
            "messages": [{"role": "system", "content": system_instruction}] + (groq_history or []),
            "temperature": 0.1,
        }
        if output_tokens is not None:
            body_preview["max_tokens"] = output_tokens
    elif provider == "claude":
        output_tokens = None
        body_preview = {
            "model": model_name,
            "conversation_messages": len(groq_history or []),
            "transport": "claude-cli",
            "generation_mode": generation_mode,
        }
    else:
        raise ValueError(
            f"Unsupported provider: {provider!r}. Expected 'gemini', 'claude', or one of "
            f"{sorted(OPENAI_COMPATIBLE_BASE_URLS)}."
        )

    body_kb = len(json.dumps(body_preview, ensure_ascii=False).encode("utf-8")) // 1024
    token_label = "max_output_tokens" if provider in {"gemini", "claude"} else "max_tokens"
    token_display = output_tokens if output_tokens is not None else "unlimited"
    print(f"  Model: {model_name}  |  Body: {body_kb} KB  |  {token_label}={token_display}")

    if debug_paths is not None:
        try:
            _debug_write_text(debug_paths["system"], system_instruction)
            if provider == "gemini":
                _debug_write_json(debug_paths["conversation"], gemini_contents or [])
            else:
                conversation_text = "\n\n".join(
                    f"[{msg.get('role', 'user').upper()}]\n{msg.get('content', '')}"
                    for msg in (groq_history or [])
                    if isinstance(msg, dict)
                )
                _debug_write_text(debug_paths["conversation"], conversation_text)
            _debug_write_json(debug_paths["request"], body_preview)
            _debug_write_text(
                debug_paths["meta"],
                f"provider={provider}\nmodel={model_name}\ngeneration_mode={generation_mode}\n",
            )
            print(f"  Debug I/O enabled ({DEBUG_IO_ENV}=1)")
            print(f"    system:       {debug_paths['system']}")
            print(f"    conversation: {debug_paths['conversation']}")
            print(f"    request:      {debug_paths['request']}")
        except Exception as exc:
            print(f"  Debug I/O write warning: {exc}")

    print("  Calling API... ", end="", flush=True)

    try:
        t0 = time.time()
        if provider == "gemini":
            if genai is None:
                sys.exit("\n[STOP] Missing dependency: google-genai. Install requirements and retry.")

            def _gemini_call() -> str:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=gemini_contents or [],
                    config={
                        "system_instruction": system_instruction,
                        "temperature": 0.1,
                    },
                )
                return _extract_gemini_text(response)

            raw_text = _invoke_with_timeout(_gemini_call, REQUEST_TIMEOUT_SECONDS)
        elif provider in OPENAI_COMPATIBLE_BASE_URLS:
            if OpenAI is None:
                sys.exit("\n[STOP] Missing dependency: openai. Install requirements and retry.")

            def _openai_compatible_call() -> str:
                client = OpenAI(
                    api_key=api_key,
                    base_url=OPENAI_COMPATIBLE_BASE_URLS[provider],
                    default_headers=_OPENAI_COMPATIBLE_EXTRA_HEADERS.get(provider),
                )
                extra_kwargs: dict = {}
                if output_tokens is not None:
                    extra_kwargs["max_tokens"] = output_tokens
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "system", "content": system_instruction}] + (groq_history or []),
                    temperature=0.1,
                    **extra_kwargs,
                )
                if not response.choices:
                    return ""
                choice = response.choices[0]
                content = choice.message.content or ""
                if not content and choice.finish_reason == "length":
                    # Only Groq gets a computed max_tokens; others send no cap.
                    print(
                        f"\n  Note: hit max_tokens={output_tokens} before any content was "
                        "emitted (finish_reason=length) -- likely a reasoning model that "
                        "spent the whole budget on internal reasoning."
                    )
                return content

            raw_text = _invoke_with_timeout(_openai_compatible_call, REQUEST_TIMEOUT_SECONDS)
        else:
            history = groq_history or []
            conversation_text = "\n\n".join(
                f"[{msg.get('role', 'user').upper()}]\n{msg.get('content', '')}"
                for msg in history
                if isinstance(msg, dict)
            )

            def _claude_call() -> tuple[str, bool]:
                return _run_claude_cli(
                    model_name=model_name,
                    system_instruction=system_instruction,
                    conversation_text=conversation_text,
                    max_output_tokens=output_tokens,
                )

            raw_text, _max_tokens_applied = _invoke_with_timeout(_claude_call, REQUEST_TIMEOUT_SECONDS)

        elapsed = time.time() - t0
        print(f"done in {elapsed:.1f}s")

        if debug_paths is not None:
            try:
                _debug_write_text(debug_paths["response"], raw_text or "")
                print(f"    response:     {debug_paths['response']}")
            except Exception as exc:
                print(f"  Debug response write warning: {exc}")
    except Exception as exc:
        print("failed")
        status_code, code, message_text = _error_details(exc)
        category = _error_category(exc)
        print(
            "  failure details: "
            f"type={category}"
            f", status={status_code or '-'}"
            f", code={code or '-'}"
            f", message={message_text}"
        )
        if _is_switchable_model_error(exc):
            if model_idx < len(models) - 1:
                model_idx += 1
                print(f"  model error/limit — switching to {models[model_idx]}")
                return "", model_idx
            sys.exit(f"\n[STOP] Exhausted all {provider} models due to limits/errors.\n  {exc}")
        sys.exit(f"\n[STOP] Request failed: {exc}")

    return (raw_text or ""), model_idx
