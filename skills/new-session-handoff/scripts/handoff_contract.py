"""Schema-derived handoff automation marker contract."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


MARKER_BLOCK_START = "HANDOFF_AUTOMATION_V1"
MARKER_BLOCK_END = "END_HANDOFF_AUTOMATION_V1"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "handoff-automation-v1.schema.json"
STRING_PLACEHOLDERS = {
    "HANDOFF_READY": "<absolute path or not-written>",
    "BLOCKERS": "none|<short reason>",
}


def load_schema(schema_path: Path = SCHEMA_PATH) -> dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


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


def extract_marker_values(path: Path, text: str) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    pattern = re.compile(
        rf"```text\n({MARKER_BLOCK_START}\n.*?{MARKER_BLOCK_END})\n```",
        re.DOTALL,
    )
    blocks = pattern.findall(text)
    if len(blocks) != 1:
        return {}, [f"{path}: expected exactly one {MARKER_BLOCK_START} block, found {len(blocks)}"]

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
    mode = values.get("HANDOFF_MODE")
    detail_state = values.get("DETAIL_ARTIFACTS_READY")
    safe = values.get("SAFE_FOR_NEW_SESSION")

    if safe == "yes":
        for field in ["DISK_STATE_RECORDED", "VALIDATION_RECORDED", "SECRET_REDACTION_CHECKED"]:
            if values.get(field) != "yes":
                errors.append(f"SAFE_FOR_NEW_SESSION=yes requires {field}=yes")
        if values.get("BLOCKERS") != "none":
            errors.append("SAFE_FOR_NEW_SESSION=yes requires BLOCKERS=none")

    if mode == "expanded":
        if detail_state not in {"yes", "no"}:
            errors.append("expanded mode requires DETAIL_ARTIFACTS_READY=yes or no")
        elif safe == "yes" and detail_state != "yes":
            errors.append("SAFE_FOR_NEW_SESSION=yes expanded handoff requires DETAIL_ARTIFACTS_READY=yes")
    elif mode in {"compact", "prompt-only"} and detail_state != "not-needed":
        errors.append(f"{mode} mode requires DETAIL_ARTIFACTS_READY=not-needed")

    return errors
