"""Schema-derived savepoint marker contract."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping


MARKER_BLOCK_START = "SAVEPOINT_V1"
MARKER_BLOCK_END = "END_SAVEPOINT_V1"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "savepoint-v1.schema.json"
STRING_PLACEHOLDERS = {
    "SAVEPOINT_PATH": "<absolute path or not-written>",
    "BLOCKERS": "none|<short reason>",
}


def load_schema(schema_path: Path = SCHEMA_PATH) -> dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8-sig"))


def marker_field_order(schema: dict[str, Any] | None = None) -> list[str]:
    schema = schema or load_schema()
    return list(schema["required"])


def marker_allowed_values(schema: dict[str, Any] | None = None) -> dict[str, set[str]]:
    schema = schema or load_schema()
    values: dict[str, set[str]] = {}
    for field, definition in schema["properties"].items():
        if "const" in definition:
            values[field] = {str(definition["const"])}
        elif "enum" in definition:
            values[field] = {str(value) for value in definition["enum"]}
    return values


def marker_template_lines(schema: dict[str, Any] | None = None) -> list[str]:
    schema = schema or load_schema()
    allowed_values = marker_allowed_values(schema)
    lines = [MARKER_BLOCK_START]
    for field in marker_field_order(schema):
        if field in allowed_values:
            value = "|".join(schema["properties"][field].get("enum", [next(iter(allowed_values[field]))]))
        else:
            value = STRING_PLACEHOLDERS.get(field, "<value>")
        lines.append(f"{field}: {value}")
    lines.append(MARKER_BLOCK_END)
    return lines


def render_marker_block(values: Mapping[str, str], schema: dict[str, Any] | None = None) -> str:
    """Render a marker block in schema order."""
    required_fields = marker_field_order(schema)
    missing = [field for field in required_fields if field not in values]
    unknown = [field for field in values if field not in required_fields]
    if missing:
        raise ValueError(f"missing marker fields: {', '.join(missing)}")
    if unknown:
        raise ValueError(f"unknown marker fields: {', '.join(unknown)}")
    lines = [MARKER_BLOCK_START]
    for field in required_fields:
        lines.append(f"{field}: {values[field]}")
    lines.append(MARKER_BLOCK_END)
    return "\n".join(lines)


def extract_marker_values(path: Path, text: str) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    pattern = re.compile(
        rf"```text\r?\n({MARKER_BLOCK_START}\r?\n.*?{MARKER_BLOCK_END})\r?\n```",
        re.DOTALL,
    )
    matches = list(pattern.finditer(text))
    blocks = [match.group(1) for match in matches]
    if len(blocks) != 1:
        return {}, [f"{path}: expected exactly one {MARKER_BLOCK_START} block, found {len(blocks)}"]
    if not text.rstrip().endswith(matches[0].group(0)):
        errors.append(f"{path}: {MARKER_BLOCK_START} block must be the final non-whitespace content")

    values: dict[str, str] = {}
    lines = blocks[0].splitlines()
    required_fields = marker_field_order()
    actual_keys = [line.split(":", 1)[0] if ":" in line else line for line in lines[1:-1]]
    if actual_keys != required_fields:
        errors.append(f"{path}: marker fields must appear exactly once in schema order")
    seen: set[str] = set()
    for line in lines[1:-1]:
        if ":" not in line:
            errors.append(f"{path}: invalid marker line {line!r}")
            continue
        key, value = line.split(":", 1)
        if key in seen:
            errors.append(f"{path}: duplicate marker {key}")
        if key not in required_fields:
            errors.append(f"{path}: unknown marker {key}")
        seen.add(key)
        values[key] = value.strip()
    return values, errors


def validate_marker_semantics(values: dict[str, str]) -> list[str]:
    """Validate cross-field marker rules that are not expressible as JSON schema enums."""
    errors: list[str] = []
    mode = values.get("SAVEPOINT_MODE")
    savepoint_ready = values.get("SAVEPOINT_PATH")
    detail_state = values.get("DETAILS_READY")
    safe = values.get("RESUME_READY")

    if safe == "yes":
        if mode != "file":
            errors.append("RESUME_READY=yes requires SAVEPOINT_MODE=file")
        for field in ["DISK_RECORDED", "VALIDATION_RECORDED", "REDACTION_CHECKED"]:
            if values.get(field) != "yes":
                errors.append(f"RESUME_READY=yes requires {field}=yes")
        if values.get("PROMPT_READY") != "yes":
            errors.append("RESUME_READY=yes requires PROMPT_READY=yes")
        if values.get("BLOCKERS") != "none":
            errors.append("RESUME_READY=yes requires BLOCKERS=none")

    if mode == "text":
        if detail_state != "not-needed":
            errors.append("text mode requires DETAILS_READY=not-needed")
        if savepoint_ready and savepoint_ready != "not-written":
            errors.append("text mode requires SAVEPOINT_PATH=not-written")
    elif mode == "file":
        if detail_state not in {"yes", "no", "not-needed"}:
            errors.append("file mode requires DETAILS_READY=yes, no, or not-needed")
        elif safe == "yes" and detail_state == "no":
            errors.append("RESUME_READY=yes requires detail artifacts ready or not-needed")
        if savepoint_ready == "not-written":
            errors.append("file mode requires SAVEPOINT_PATH to point to SAVEPOINT.md")
        elif savepoint_ready and not _is_absolute_savepoint_path(savepoint_ready):
            errors.append("file mode requires SAVEPOINT_PATH to be an absolute path to SAVEPOINT.md")
    elif mode:
        errors.append(f"unknown SAVEPOINT_MODE={mode}")

    return errors


def _is_absolute_savepoint_path(value: str) -> bool:
    if not value.endswith("/SAVEPOINT.md") and not value.endswith("\\SAVEPOINT.md"):
        return False
    return value.startswith("/") or bool(re.match(r"^[A-Za-z]:[\\/]", value))
