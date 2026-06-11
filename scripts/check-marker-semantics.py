#!/usr/bin/env python3
"""Validate cross-field savepoint marker semantics."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "skills" / "savepoint" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from savepoint_contract import extract_marker_values, validate_marker_semantics  # noqa: E402
from validate_savepoint import scan_secret_patterns, validate_savepoint  # noqa: E402


BASE_VALUES = {
    "SAVEPOINT_MODE": "file",
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
    errors.extend(expect("safe file", {}, True))
    errors.extend(
        expect(
            "unsafe file with details not ready",
            {
                "DETAILS_READY": "no",
                "RESUME_READY": "no",
            },
            True,
        )
    )
    errors.extend(
        expect(
            "safe file rejects details not ready",
            {"DETAILS_READY": "no"},
            False,
        )
    )
    errors.extend(
        expect(
            "text is never resume ready",
            {
                "SAVEPOINT_MODE": "text",
                "SAVEPOINT_PATH": "not-written",
                "DETAILS_READY": "not-needed",
            },
            False,
        )
    )
    errors.extend(
        expect(
            "unsafe /savepoint text marker block is valid",
            {
                "SAVEPOINT_MODE": "text",
                "SAVEPOINT_PATH": "not-written",
                "DETAILS_READY": "not-needed",
                "DISK_RECORDED": "no",
                "VALIDATION_RECORDED": "no",
                "RESUME_READY": "no",
                "BLOCKERS": "text-savepoint-no-repo-recovery",
            },
            True,
        )
    )
    errors.extend(
        expect(
            "text rejects detail artifacts",
            {
                "SAVEPOINT_MODE": "text",
                "DETAILS_READY": "yes",
                "RESUME_READY": "no",
            },
            False,
        )
    )
    errors.extend(
        expect(
            "file requires written savepoint path",
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
    errors.extend(check_text_details_reference_rejected())
    errors.extend(check_prompt_ready_requires_prompt_evidence())
    errors.extend(check_embedded_resume_prompt_satisfies_prompt_ready())
    errors.extend(check_marker_must_be_final())
    errors.extend(check_marker_parser_accepts_crlf())
    errors.extend(check_file_path_must_exist_without_example_flag())
    errors.extend(check_resume_ready_requires_substantive_values())
    errors.extend(check_resume_ready_rejects_none_for_required_value())
    errors.extend(check_resume_ready_allows_none_for_absence_value())
    errors.extend(check_resume_ready_rejects_indented_required_labels())
    errors.extend(check_resume_ready_rejects_unindented_continuation())
    errors.extend(check_resume_ready_accepts_indented_continuation())
    errors.extend(check_secret_scanner_flags_common_tokens())
    errors.extend(check_secret_scanner_allows_redacted_values())
    errors.extend(check_secret_scanner_rejects_non_placeholder_redacted_values())

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("ok: marker semantics")
    return 0


def marker_block(**overrides: str) -> str:
    values = {
        "SAVEPOINT_PATH": "/tmp/SAVEPOINT.md",
        "SAVEPOINT_MODE": "file",
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


def check_text_details_reference_rejected() -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SAVEPOINT.md"
        path.write_text(
            minimal_savepoint(
                marker_block(
                    SAVEPOINT_MODE="text",
                    DETAILS_READY="not-needed",
                    SAVEPOINT_PATH="not-written",
                    RESUME_READY="no",
                    BLOCKERS="text-savepoint-no-repo-recovery",
                ),
                detail_reference="- `details/changed-files.md` - should not be here",
            ),
            encoding="utf-8",
        )
        errors = validate_savepoint(path, allow_example_paths=True)
    if not any("text mode must not reference detail artifacts" in error for error in errors):
        return [
            "/savepoint text with detail references should fail, "
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


def check_marker_parser_accepts_crlf() -> list[str]:
    text = f"```text\n{marker_block()}\n```\n".replace("\n", "\r\n")
    values, errors = extract_marker_values(Path("crlf-savepoint.md"), text)
    if errors or values.get("SAVEPOINT_MODE") != "file":
        return [f"CRLF marker block should parse, got values={values}, errors={errors}"]
    return []


def check_file_path_must_exist_without_example_flag() -> list[str]:
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


def check_resume_ready_rejects_none_for_required_value() -> list[str]:
    source = ROOT / "examples" / "file-bugfix" / "SAVEPOINT.md"
    text = source.read_text(encoding="utf-8")
    text = text.replace(
        "- Goal: Fix a null-token crash in login without changing the auth API.",
        "- Goal: none",
        1,
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SAVEPOINT.md"
        path.write_text(text, encoding="utf-8")
        errors = validate_savepoint(path, allow_example_paths=True)
    if not any("substantive value for - Goal:" in error for error in errors):
        return [
            "RESUME_READY=yes should reject 'none' for required Goal, "
            f"got errors={errors}"
        ]
    return []


def check_resume_ready_allows_none_for_absence_value() -> list[str]:
    source = ROOT / "examples" / "file-bugfix" / "SAVEPOINT.md"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SAVEPOINT.md"
        path.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        errors = validate_savepoint(path, allow_example_paths=True)
    blocker_errors = [
        error for error in errors if "substantive value for - Blocker:" in error
    ]
    if blocker_errors:
        return [
            "RESUME_READY=yes should allow 'none' for absence-only Blocker, "
            f"got errors={errors}"
        ]
    return []


def check_resume_ready_rejects_indented_required_labels() -> list[str]:
    source = ROOT / "examples" / "file-bugfix" / "SAVEPOINT.md"
    text = source.read_text(encoding="utf-8").replace(
        "- Goal: Fix a null-token crash in login without changing the auth API.",
        "  - Goal: Fix a null-token crash in login without changing the auth API.",
        1,
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SAVEPOINT.md"
        path.write_text(text, encoding="utf-8")
        errors = validate_savepoint(path, allow_example_paths=True)
    if not any("substantive value for - Goal:" in error for error in errors):
        return [
            "RESUME_READY=yes should reject indented required labels, "
            f"got errors={errors}"
        ]
    return []


def check_resume_ready_rejects_unindented_continuation() -> list[str]:
    source = ROOT / "examples" / "file-bugfix" / "SAVEPOINT.md"
    text = source.read_text(encoding="utf-8").replace(
        "- Goal: Fix a null-token crash in login without changing the auth API.",
        "- Goal:\nMalformed unindented continuation accepted as a value.",
        1,
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SAVEPOINT.md"
        path.write_text(text, encoding="utf-8")
        errors = validate_savepoint(path, allow_example_paths=True)
    if not any("substantive value for - Goal:" in error for error in errors):
        return [
            "RESUME_READY=yes should reject unindented continuation after an empty label, "
            f"got errors={errors}"
        ]
    return []


def check_resume_ready_accepts_indented_continuation() -> list[str]:
    source = ROOT / "examples" / "file-bugfix" / "SAVEPOINT.md"
    text = source.read_text(encoding="utf-8").replace(
        "- Goal: Fix a null-token crash in login without changing the auth API.",
        "- Goal:\n  Fix a null-token crash in login without changing the auth API.",
        1,
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SAVEPOINT.md"
        path.write_text(text, encoding="utf-8")
        errors = validate_savepoint(path, allow_example_paths=True)
    if any("substantive value for - Goal:" in error for error in errors):
        return [
            "RESUME_READY=yes should accept indented continuation after a required label, "
            f"got errors={errors}"
        ]
    return []


def check_secret_scanner_flags_common_tokens() -> list[str]:
    samples = {
        "github fine-grained token": "github_pat_" + "A" * 24,
        "github oauth token": "gho_" + "B" * 24,
        "github user token": "ghu_" + "C" * 24,
        "github server token": "ghs_" + "D" * 24,
        "slack token": "xoxb-" + "E" * 12 + "-" + "F" * 12,
        "google oauth token": "ya29." + "G" * 24,
        "bearer header": "Authorization: Bearer " + "h" * 24,
        "jwt": "eyJ" + "a" * 12 + "." + "b" * 12 + "." + "c" * 12,
    }
    errors: list[str] = []
    for name, text in samples.items():
        scan_errors: list[str] = []
        scan_secret_patterns(Path(f"{name}.txt"), text, scan_errors)
        if not scan_errors:
            errors.append(f"secret scanner should flag {name}")
    return errors


def check_secret_scanner_allows_redacted_values() -> list[str]:
    text = "\n".join(
        [
            'token="<REDACTED>"',
            "api_key='<REDACTED>'",
            'password="REDACTED"',
            'secret="***"',
            "Authorization: Bearer <REDACTED>",
        ]
    )
    errors: list[str] = []
    scan_secret_patterns(Path("redacted.txt"), text, errors)
    if errors:
        return [f"redacted secret placeholders should not be flagged, got errors={errors}"]
    return []


def check_secret_scanner_rejects_non_placeholder_redacted_values() -> list[str]:
    samples = {
        "redacted substring": 'token="redacted-but-not-placeholder"',
        "starred substring": 'password="abc***def"',
    }
    errors: list[str] = []
    for name, text in samples.items():
        scan_errors: list[str] = []
        scan_secret_patterns(Path(f"{name}.txt"), text, scan_errors)
        if not scan_errors:
            errors.append(f"secret scanner should reject non-placeholder {name}")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
