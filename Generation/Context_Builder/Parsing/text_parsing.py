from __future__ import annotations


def strip_code_fences(text: str) -> str:
    """Remove optional markdown code fences from LLM output text."""
    value = text.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        value = "\n".join(lines).strip()
    return value


def extract_outer_json_object(text: str) -> str:
    """Extract the outer-most JSON object from text by tracking brace depth.

    Uses brace counting rather than rfind so that explanation text appended by
    the model after the closing brace (which may itself contain braces) does not
    corrupt the extracted slice.
    """
    cleaned = strip_code_fences(text)
    start = cleaned.find("{")
    if start == -1:
        return cleaned

    depth = 0
    in_string = False
    escape_next = False
    for i, ch in enumerate(cleaned[start:], start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return cleaned[start : i + 1]

    # Brace counting failed (unbalanced JSON) — fall back to first/last brace slice.
    end = cleaned.rfind("}")
    if end >= start:
        return cleaned[start : end + 1]
    return cleaned
