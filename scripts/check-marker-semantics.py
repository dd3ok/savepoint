#!/usr/bin/env python3
"""Validate cross-field savepoint marker semantics."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "skills" / "savepoint" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from savepoint_contract import validate_marker_semantics  # noqa: E402
from validate_savepoint import validate_savepoint  # noqa: E402


BASE_VALUES = {
    "SAVEPOINT_MODE": "verified",
    "SAVEPOINT_PATH": "/tmp/SAVEPOINT.md",
    "DETAILS_READY": "not-needed",
    "DISK_RECORDED": "yes",
    "VALIDATION_RECORDED": "yes",
    "REDACTION_CHECKED": "yes",
    "PROMPT_READY": "yes",
    "RESUME_READY": "yes",
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
    errors.extend(expect("safe verified", {}, True))
    errors.extend(
        expect(
            "unsafe verified with details not ready",
            {
                "DETAILS_READY": "no",
                "RESUME_READY": "no",
            },
            True,
        )
    )
    errors.extend(
        expect(
            "safe verified rejects details not ready",
            {"DETAILS_READY": "no"},
            False,
        )
    )
    errors.extend(
        expect(
            "lightweight is never resume ready",
            {
                "SAVEPOINT_MODE": "lightweight",
                "SAVEPOINT_PATH": "not-written",
                "DETAILS_READY": "not-needed",
            },
            False,
        )
    )
    errors.extend(
        expect(
            "unsafe lightweight note is valid",
            {
                "SAVEPOINT_MODE": "lightweight",
                "SAVEPOINT_PATH": "not-written",
                "DETAILS_READY": "not-needed",
                "DISK_RECORDED": "no",
                "VALIDATION_RECORDED": "no",
                "RESUME_READY": "no",
                "BLOCKERS": "lightweight-note-no-repo-recovery",
            },
            True,
        )
    )
    errors.extend(
        expect(
            "lightweight rejects detail artifacts",
            {
                "SAVEPOINT_MODE": "lightweight",
                "DETAILS_READY": "yes",
                "RESUME_READY": "no",
            },
            False,
        )
    )
    errors.extend(
        expect(
            "verified requires written savepoint path",
            {"SAVEPOINT_PATH": "not-written", "RESUME_READY": "no"},
            False,
        )
    )
    errors.extend(
        expect(
            "written savepoint path must be absolute",
            {"SAVEPOINT_PATH": "SAVEPOINT.md", "RESUME_READY": "no"},
            False,
        )
    )
    errors.extend(
        expect(
            "written savepoint path must point to SAVEPOINT.md",
            {"SAVEPOINT_PATH": "/tmp/NOTES.md", "RESUME_READY": "no"},
            False,
        )
    )
    errors.extend(expect("safe requires no blockers", {"BLOCKERS": "waiting-for-user"}, False))
    errors.extend(expect("safe requires prompt ready", {"PROMPT_READY": "no"}, False))
    errors.extend(check_detail_reference_required())
    errors.extend(check_lightweight_details_reference_rejected())
    errors.extend(check_prompt_ready_requires_prompt_evidence())
    errors.extend(check_embedded_resume_prompt_satisfies_prompt_ready())
    errors.extend(check_marker_must_be_final())
    errors.extend(check_verified_path_must_exist_without_example_flag())
    errors.extend(check_resume_ready_requires_substantive_values())

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("ok: marker semantics")
    return 0


def marker_block(**overrides: str) -> str:
    values = {
        "SAVEPOINT_PATH": "/tmp/SAVEPOINT.md",
        "SAVEPOINT_MODE": "verified",
        "DETAILS_READY": "yes",
        "PROMPT_READY": "yes",
        "DISK_RECORDED": "yes",
        "VALIDATION_RECORDED": "yes",
        "REDACTION_CHECKED": "yes",
        "RESUME_READY": "yes",
        "BLOCKERS": "none",
    }
    values.update(overrides)
    lines = ["SAVEPOINT_V1"]
    lines.extend(f"{key}: {value}" for key, value in values.items())
    lines.append("END_SAVEPOINT_V1")
    return "\n".join(lines)


def minimal_savepoint(block: str, detail_reference: str = "", resume_prompt: bool = False) -> str:
    prompt_section = (
        """
## Resume Prompt

```text
Continue from this savepoint after verifying disk state.
```
"""
        if resume_prompt
        else ""
    )
    return f"""# Test Savepoint

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


def check_detail_reference_required() -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SAVEPOINT.md"
        path.write_text(minimal_savepoint(marker_block()), encoding="utf-8")
        errors = validate_savepoint(path, allow_example_paths=True)
    if not any("requires at least one detail artifact reference" in error for error in errors):
        return [
            "details-ready savepoint without detail references should fail, "
            f"got errors={errors}"
        ]
    return []


def check_lightweight_details_reference_rejected() -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SAVEPOINT.md"
        path.write_text(
            minimal_savepoint(
                marker_block(
                    SAVEPOINT_MODE="lightweight",
                    DETAILS_READY="not-needed",
                    SAVEPOINT_PATH="not-written",
                    RESUME_READY="no",
                    BLOCKERS="lightweight-note-no-repo-recovery",
                ),
                detail_reference="- `details/changed-files.md` - should not be here",
            ),
            encoding="utf-8",
        )
        errors = validate_savepoint(path, allow_example_paths=True)
    if not any("lightweight mode must not reference detail artifacts" in error for error in errors):
        return [
            "lightweight savepoint with detail references should fail, "
            f"got errors={errors}"
        ]
    return []


def check_prompt_ready_requires_prompt_evidence() -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SAVEPOINT.md"
        path.write_text(
            minimal_savepoint(
                marker_block(
                    DETAILS_READY="not-needed",
                    SAVEPOINT_PATH="/tmp/SAVEPOINT.md",
                )
            ),
            encoding="utf-8",
        )
        errors = validate_savepoint(path, allow_example_paths=True)
    if not any("PROMPT_READY=yes requires" in error for error in errors):
        return [
            "prompt-ready savepoint without prompt evidence should fail, "
            f"got errors={errors}"
        ]
    return []


def check_embedded_resume_prompt_satisfies_prompt_ready() -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SAVEPOINT.md"
        path.write_text(
            minimal_savepoint(
                marker_block(
                    DETAILS_READY="not-needed",
                    SAVEPOINT_PATH="/tmp/SAVEPOINT.md",
                ),
                resume_prompt=True,
            ),
            encoding="utf-8",
        )
        errors = validate_savepoint(path, allow_example_paths=True)
    prompt_errors = [
        error for error in errors if "PROMPT_READY=yes requires" in error
    ]
    if prompt_errors:
        return [
            "embedded Resume Prompt should satisfy prompt-ready evidence, "
            f"got errors={errors}"
        ]
    return []


def check_marker_must_be_final() -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SAVEPOINT.md"
        path.write_text(
            minimal_savepoint(
                marker_block(
                    DETAILS_READY="not-needed",
                    SAVEPOINT_PATH="/tmp/SAVEPOINT.md",
                ),
                resume_prompt=True,
            )
            + "\nExtra trailing content\n",
            encoding="utf-8",
        )
        errors = validate_savepoint(path, allow_example_paths=True)
    if not any("block must be the final non-whitespace content" in error for error in errors):
        return [
            "savepoint with content after marker should fail, "
            f"got errors={errors}"
        ]
    return []


def check_verified_path_must_exist_without_example_flag() -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SAVEPOINT.md"
        path.write_text(
            minimal_savepoint(
                marker_block(
                    DETAILS_READY="not-needed",
                    SAVEPOINT_PATH="/tmp/SAVEPOINT.md",
                ),
                resume_prompt=True,
            ),
            encoding="utf-8",
        )
        errors = validate_savepoint(path)
    if not any("SAVEPOINT_PATH does not exist" in error for error in errors):
        return [
            "non-example validation should reject missing SAVEPOINT_PATH, "
            f"got errors={errors}"
        ]
    return []


def check_resume_ready_requires_substantive_values() -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SAVEPOINT.md"
        path.write_text(
            minimal_savepoint(
                marker_block(
                    DETAILS_READY="not-needed",
                    SAVEPOINT_PATH="/tmp/SAVEPOINT.md",
                ),
                resume_prompt=True,
            ),
            encoding="utf-8",
        )
        errors = validate_savepoint(path, allow_example_paths=True)
    if not any("RESUME_READY=yes requires substantive value" in error for error in errors):
        return [
            "RESUME_READY=yes with empty recovery fields should fail, "
            f"got errors={errors}"
        ]
    return []


if __name__ == "__main__":
    raise SystemExit(main())
