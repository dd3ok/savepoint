#!/usr/bin/env python3
"""Validate cross-field automation marker semantics."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "skills" / "new-session-handoff" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from handoff_contract import validate_marker_semantics  # noqa: E402
from validate_handoff import validate_handoff  # noqa: E402


BASE_VALUES = {
    "HANDOFF_MODE": "compact",
    "HANDOFF_READY": "/tmp/HANDOFF.md",
    "DETAIL_ARTIFACTS_READY": "not-needed",
    "DISK_STATE_RECORDED": "yes",
    "VALIDATION_RECORDED": "yes",
    "SECRET_REDACTION_CHECKED": "yes",
    "NEW_SESSION_PROMPT_READY": "yes",
    "SAFE_FOR_NEW_SESSION": "yes",
    "BLOCKERS": "none",
}


def expect(name: str, values: dict[str, str], should_pass: bool) -> list[str]:
    merged = {**BASE_VALUES, **values}
    errors = validate_marker_semantics(merged)
    passed = not errors
    if passed != should_pass:
        return [f"{name}: expected pass={should_pass}, got errors={errors}"]
    return []


def main() -> int:
    errors: list[str] = []
    errors.extend(expect("safe compact", {}, True))
    errors.extend(
        expect(
            "unsafe expanded with details not ready",
            {
                "HANDOFF_MODE": "expanded",
                "DETAIL_ARTIFACTS_READY": "no",
                "SAFE_FOR_NEW_SESSION": "no",
            },
            True,
        )
    )
    errors.extend(
        expect(
            "safe expanded requires details ready",
            {"HANDOFF_MODE": "expanded", "DETAIL_ARTIFACTS_READY": "no"},
            False,
        )
    )
    errors.extend(
        expect(
            "unsafe compact still requires not-needed details",
            {"DETAIL_ARTIFACTS_READY": "yes", "SAFE_FOR_NEW_SESSION": "no"},
            False,
        )
    )
    errors.extend(
        expect(
            "unsafe prompt-only still requires not-needed details",
            {
                "HANDOFF_MODE": "prompt-only",
                "DETAIL_ARTIFACTS_READY": "no",
                "SAFE_FOR_NEW_SESSION": "no",
            },
            False,
        )
    )
    errors.extend(
        expect(
            "prompt-only requires not-written handoff path",
            {
                "HANDOFF_MODE": "prompt-only",
                "HANDOFF_READY": "/tmp/HANDOFF.md",
                "SAFE_FOR_NEW_SESSION": "no",
            },
            False,
        )
    )
    errors.extend(
        expect(
            "compact requires written handoff path",
            {"HANDOFF_READY": "not-written", "SAFE_FOR_NEW_SESSION": "no"},
            False,
        )
    )
    errors.extend(
        expect(
            "written handoff path must be absolute",
            {"HANDOFF_READY": "HANDOFF.md", "SAFE_FOR_NEW_SESSION": "no"},
            False,
        )
    )
    errors.extend(
        expect(
            "written handoff path must point to HANDOFF.md",
            {"HANDOFF_READY": "/tmp/NOTES.md", "SAFE_FOR_NEW_SESSION": "no"},
            False,
        )
    )
    errors.extend(
        expect(
            "safe requires no blockers",
            {"BLOCKERS": "waiting-for-user"},
            False,
        )
    )
    errors.extend(
        expect(
            "safe requires prompt ready",
            {"NEW_SESSION_PROMPT_READY": "no"},
            False,
        )
    )
    errors.extend(check_expanded_details_reference_required())
    errors.extend(check_compact_details_reference_rejected())
    errors.extend(check_prompt_ready_requires_prompt_evidence())
    errors.extend(check_embedded_resume_prompt_satisfies_prompt_ready())

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("ok: marker semantics")
    return 0


def marker_block(**overrides: str) -> str:
    values = {
        "HANDOFF_READY": "/tmp/HANDOFF.md",
        "HANDOFF_SCHEMA_VERSION": "1",
        "HANDOFF_MODE": "expanded",
        "DETAIL_ARTIFACTS_READY": "yes",
        "NEW_SESSION_PROMPT_READY": "yes",
        "DISK_STATE_RECORDED": "yes",
        "VALIDATION_RECORDED": "yes",
        "SECRET_REDACTION_CHECKED": "yes",
        "SAFE_FOR_NEW_SESSION": "yes",
        "BLOCKERS": "none",
    }
    values.update(overrides)
    lines = ["HANDOFF_AUTOMATION_V1"]
    lines.extend(f"{key}: {value}" for key, value in values.items())
    lines.append("END_HANDOFF_AUTOMATION_V1")
    return "\n".join(lines)


def minimal_handoff(block: str, detail_reference: str = "", resume_prompt: bool = False) -> str:
    prompt_section = (
        """
## Resume Prompt

```text
Continue from this handoff after verifying disk state.
```
"""
        if resume_prompt
        else ""
    )
    return f"""# Test Handoff

## TL;DR / Operational Summary

- Goal:
- Current state:
- Next action:
- Blocker:

## Required Reading

{detail_reference}
{prompt_section}

## Validation Manifest

- Secret redaction check: manual

```text
{block}
```
"""


def check_expanded_details_reference_required() -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "HANDOFF.md"
        path.write_text(minimal_handoff(marker_block()), encoding="utf-8")
        errors = validate_handoff(path)
    if not any("requires at least one detail artifact reference" in error for error in errors):
        return [
            "expanded details-ready handoff without detail references should fail, "
            f"got errors={errors}"
        ]
    return []


def check_compact_details_reference_rejected() -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "HANDOFF.md"
        path.write_text(
            minimal_handoff(
                marker_block(
                    HANDOFF_MODE="compact",
                    DETAIL_ARTIFACTS_READY="not-needed",
                    HANDOFF_READY="/tmp/HANDOFF.md",
                ),
                detail_reference="- `details/changed-files.md` - should not be here",
                resume_prompt=True,
            ),
            encoding="utf-8",
        )
        errors = validate_handoff(path)
    if not any("compact mode must not reference detail artifacts" in error for error in errors):
        return [
            "compact handoff with detail references should fail, "
            f"got errors={errors}"
        ]
    return []


def check_prompt_ready_requires_prompt_evidence() -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "HANDOFF.md"
        path.write_text(
            minimal_handoff(
                marker_block(
                    HANDOFF_MODE="compact",
                    DETAIL_ARTIFACTS_READY="not-needed",
                    HANDOFF_READY="/tmp/HANDOFF.md",
                )
            ),
            encoding="utf-8",
        )
        errors = validate_handoff(path)
    if not any("NEW_SESSION_PROMPT_READY=yes requires" in error for error in errors):
        return [
            "prompt-ready handoff without prompt evidence should fail, "
            f"got errors={errors}"
        ]
    return []


def check_embedded_resume_prompt_satisfies_prompt_ready() -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "HANDOFF.md"
        path.write_text(
            minimal_handoff(
                marker_block(
                    HANDOFF_MODE="compact",
                    DETAIL_ARTIFACTS_READY="not-needed",
                    HANDOFF_READY="/tmp/HANDOFF.md",
                ),
                resume_prompt=True,
            ),
            encoding="utf-8",
        )
        errors = validate_handoff(path)
    prompt_errors = [
        error for error in errors if "NEW_SESSION_PROMPT_READY=yes requires" in error
    ]
    if prompt_errors:
        return [
            "embedded Resume Prompt should satisfy prompt-ready evidence, "
            f"got errors={errors}"
        ]
    return []


if __name__ == "__main__":
    raise SystemExit(main())
