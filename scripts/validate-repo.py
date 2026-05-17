#!/usr/bin/env python3
"""Validate the handoff skill repository contract."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "new-session-handoff"
SKILL_SCRIPTS = SKILL_DIR / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from handoff_contract import (  # noqa: E402
    MARKER_BLOCK_END,
    MARKER_BLOCK_START,
    marker_allowed_values,
    marker_field_order,
    marker_template_lines,
    validate_marker_semantics,
)

EXPECTED_MARKER_LINES = [
    "HANDOFF_AUTOMATION_V1",
    "HANDOFF_READY: <absolute path or not-written>",
    "HANDOFF_SCHEMA_VERSION: 1",
    "HANDOFF_MODE: compact|expanded|prompt-only",
    "DETAIL_ARTIFACTS_READY: yes|no|not-needed",
    "NEW_SESSION_PROMPT_READY: yes|no",
    "DISK_STATE_RECORDED: yes|no",
    "VALIDATION_RECORDED: yes|no",
    "SECRET_REDACTION_CHECKED: yes|no",
    "SAFE_FOR_NEW_SESSION: yes|no",
    "BLOCKERS: none|<short reason>",
    "END_HANDOFF_AUTOMATION_V1",
]
HANDOFF_FILES = [
    SKILL_DIR / "references" / "handoff-template.md",
    ROOT / "examples" / "HANDOFF.filled.example.md",
    ROOT / "examples" / "compact-bugfix" / "HANDOFF.md",
    ROOT / "examples" / "expanded-architecture" / "HANDOFF.md",
    ROOT / "examples" / "unsafe-handoff" / "HANDOFF.md",
]
CANONICAL_REFERENCES = [
    "context-packaging.md",
    "handoff-contract.md",
    "handoff-template.md",
]
MARKER_ENUMS = {
    "HANDOFF_SCHEMA_VERSION": {"1"},
    "HANDOFF_MODE": {"compact", "expanded", "prompt-only"},
    "DETAIL_ARTIFACTS_READY": {"yes", "no", "not-needed"},
    "NEW_SESSION_PROMPT_READY": {"yes", "no"},
    "DISK_STATE_RECORDED": {"yes", "no"},
    "VALIDATION_RECORDED": {"yes", "no"},
    "SECRET_REDACTION_CHECKED": {"yes", "no"},
    "SAFE_FOR_NEW_SESSION": {"yes", "no"},
}
TRUST_ORDER_LINES = [
    "1. Current explicit user instruction in this session.",
    "2. Current working tree and Git state.",
    "3. Repository instruction files and durable state files such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_STATE.md`, `TASKS.md`, `DECISIONS.md`, `PLAN.md`, and `PLANS.md`.",
    "4. `HANDOFF.md`.",
    "5. Focused detail artifacts referenced by `HANDOFF.md`.",
    "6. Prior chat history only if explicitly provided by the user.",
]
KOREAN_INVOCATION_PHRASES = [
    "핸드오프 만들어줘",
    "핸드오프 읽고 이어서 해줘",
]


class Validator:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def fail(self, message: str) -> None:
        self.errors.append(message)

    def require_exists(self, path: Path) -> None:
        if not path.exists():
            self.fail(f"missing required path: {path.relative_to(ROOT)}")

    def read(self, path: Path) -> str:
        self.require_exists(path)
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def validate_frontmatter(self) -> None:
        path = SKILL_DIR / "SKILL.md"
        text = self.read(path)
        lines = text.splitlines()
        if len(lines) < 4 or lines[0] != "---":
            self.fail("SKILL.md must start with YAML frontmatter delimiter")
            return
        try:
            end = lines[1:].index("---") + 1
        except ValueError:
            self.fail("SKILL.md frontmatter closing delimiter is missing")
            return

        frontmatter = lines[1:end]
        data: dict[str, str] = {}
        for line in frontmatter:
            if ":" not in line:
                self.fail(f"invalid frontmatter line: {line}")
                continue
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')

        name = data.get("name", "")
        description = data.get("description", "")
        if set(data) != {"name", "description"}:
            self.fail("SKILL.md frontmatter must contain only name and description")
        if name != SKILL_DIR.name:
            self.fail(f"frontmatter name must match skill directory: {name!r}")
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?", name):
            self.fail(f"frontmatter name has invalid format: {name!r}")
        if not description:
            self.fail("frontmatter description is required")
        if len(description) > 1024:
            self.fail("frontmatter description exceeds 1024 characters")
        lower_description = description.lower()
        if "explicit" not in lower_description:
            self.fail("frontmatter description must limit use to explicit user requests")
        if "/new" not in lower_description or "pty" not in lower_description:
            self.fail("frontmatter description must state the session-control boundary")
        for phrase in KOREAN_INVOCATION_PHRASES:
            if phrase not in description:
                self.fail(f"frontmatter description must include Korean invocation phrase: {phrase}")
        body = "\n".join(lines[end + 1 :])
        if not body.strip().startswith("# New Session Handoff"):
            self.fail("SKILL.md body should start with '# New Session Handoff'")

    def validate_references(self) -> None:
        skill_text = self.read(SKILL_DIR / "SKILL.md")
        for ref in sorted(set(re.findall(r"`(references/[^`]+)`", skill_text))):
            if "*" in ref:
                continue
            self.require_exists(SKILL_DIR / ref)
        for name in CANONICAL_REFERENCES:
            self.require_exists(SKILL_DIR / "references" / name)
        self.require_exists(SKILL_DIR / "schemas" / "handoff-automation-v1.schema.json")
        openai_yaml = self.read(SKILL_DIR / "agents" / "openai.yaml")
        if "allow_implicit_invocation" in openai_yaml:
            self.fail("agents/openai.yaml must not use unvalidated allow_implicit_invocation policy")
        required_skill_phrases = [
            ".new-session-handoff/HANDOFF.md",
            "Embed the resume prompt inside `HANDOFF.md`",
            "delete only untracked generated handoff artifacts",
            "Durable state files are not generated detail artifacts",
            "A handoff is adopted only after",
            "For inspect-only requests, do not clean up by default.",
        ]
        for phrase in required_skill_phrases:
            if phrase not in skill_text:
                self.fail(f"SKILL.md missing lightweight default policy: {phrase}")

        contract_text = self.read(SKILL_DIR / "references" / "handoff-contract.md")
        required_contract_phrases = [
            ".new-session-handoff/HANDOFF.md",
            "NEW_SESSION_PROMPT_READY",
            "embedded",
            "legacy `HANDOFF.md`",
            "Do not delete tracked files",
            "relevant durable state files",
            "Durable state files are not generated detail artifacts",
            "cleanup happens only after adoption",
            "Cleanup scope is limited to the selected generated handoff",
        ]
        for phrase in required_contract_phrases:
            if phrase not in contract_text:
                self.fail(f"handoff-contract.md missing lightweight policy: {phrase}")

        template_text = self.read(SKILL_DIR / "references" / "handoff-template.md")
        if "## Resume Prompt" not in template_text:
            self.fail("handoff-template.md must embed a Resume Prompt section")
        if "## Fresh Session Prompt" in template_text:
            self.fail("handoff-template.md should use Resume Prompt, not Fresh Session Prompt")
        cleanup_eval_text = self.read(ROOT / "evals" / "cases" / "resume-cleanup.md")
        for phrase in [
            "only after adoption",
            "inspect-only",
            "external-path",
            "Reports removed paths, kept paths, and reasons.",
        ]:
            if phrase not in cleanup_eval_text:
                self.fail(f"evals/cases/resume-cleanup.md missing cleanup policy phrase: {phrase}")

    def validate_readme_format(self) -> None:
        readme_text = self.read(ROOT / "README.md")
        lines = readme_text.splitlines()
        first_line = lines[0] if lines else ""
        stripped_readme = readme_text.strip()
        if stripped_readme.startswith('"""') or stripped_readme.endswith('"""'):
            self.fail("README.md must not be wrapped in triple quotes")
        if first_line != "# New Session Handoff Skill":
            self.fail("README.md must start with '# New Session Handoff Skill'")
        for phrase in [
            "skills/new-session-handoff/references/context-packaging.md",
            "evals/trigger-queries.json",
            "evals/cases/context-state-bridge.md",
            "evals/cases/trigger-boundaries.md",
        ]:
            if phrase not in readme_text:
                self.fail(f"README.md missing repository map entry: {phrase}")

    def validate_trigger_evals(self) -> None:
        path = ROOT / "evals" / "trigger-queries.json"
        self.require_exists(path)

        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.fail(f"evals/trigger-queries.json is invalid JSON: {exc}")
            return

        queries = data.get("queries", [])
        if data.get("skill_name") != "new-session-handoff":
            self.fail("evals/trigger-queries.json skill_name must be new-session-handoff")
        if data.get("version") != 1:
            self.fail("evals/trigger-queries.json version must be 1")
        if not isinstance(queries, list):
            self.fail("evals/trigger-queries.json queries must be a list")
            return
        if len(queries) < 16:
            self.fail("evals/trigger-queries.json should contain at least 16 trigger queries")

        required_fields = {"id", "query", "should_trigger", "language", "category", "rationale"}
        seen_ids: set[str] = set()
        positives = 0
        negatives = 0
        has_korean_handoff_positive = False
        has_korean_negative = False
        has_secret_redaction_positive = False
        present_negative_categories: set[str] = set()
        for index, query in enumerate(queries):
            if not isinstance(query, dict):
                self.fail(f"trigger eval query #{index} must be an object")
                continue
            missing = required_fields - set(query)
            if missing:
                self.fail(f"trigger eval query #{index} missing fields: {sorted(missing)}")

            query_id = query.get("id")
            if not isinstance(query_id, str) or not query_id.strip():
                self.fail(f"trigger eval query #{index} has invalid id")
            elif query_id in seen_ids:
                self.fail(f"evals/trigger-queries.json contains duplicate id: {query_id}")
            else:
                seen_ids.add(query_id)

            query_text = query.get("query")
            if not isinstance(query_text, str) or not query_text.strip():
                self.fail(f"trigger eval query #{index} has empty query")

            should_trigger = query.get("should_trigger")
            category = query.get("category")
            if should_trigger is True:
                positives += 1
                if isinstance(query_text, str) and "핸드오프" in query_text:
                    has_korean_handoff_positive = True
                if category == "secret-redaction":
                    has_secret_redaction_positive = True
            elif should_trigger is False:
                negatives += 1
                if query.get("language") == "ko":
                    has_korean_negative = True
                if isinstance(category, str):
                    present_negative_categories.add(category)
            else:
                self.fail(f"trigger eval query #{index} should_trigger must be boolean")

            if query.get("language") not in {"en", "ko"}:
                self.fail(f"trigger eval query #{index} language must be en or ko")
            if not isinstance(category, str) or not category.strip():
                self.fail(f"trigger eval query #{index} has empty category")
            if not isinstance(query.get("rationale"), str) or not query["rationale"].strip():
                self.fail(f"trigger eval query #{index} has empty rationale")

        if positives < 8:
            self.fail("trigger evals should include at least 8 should_trigger=true queries")
        if negatives < 8:
            self.fail("trigger evals should include at least 8 should_trigger=false queries")
        if not has_korean_handoff_positive:
            self.fail("trigger evals should include Korean handoff trigger queries")
        if not has_korean_negative:
            self.fail("trigger evals should include Korean near-miss negative queries")
        if not has_secret_redaction_positive:
            self.fail("trigger evals should include secret-bearing handoff requests as should_trigger=true")

        near_miss_categories = {
            "ordinary-summary",
            "repo-instructions",
            "implementation",
            "session-control",
            "status-command",
            "state-file-authoring",
        }
        missing_near_misses = near_miss_categories - present_negative_categories
        if missing_near_misses:
            self.fail(f"trigger evals missing near-miss negative categories: {sorted(missing_near_misses)}")

        for case_name in ["context-state-bridge.md", "trigger-boundaries.md"]:
            self.require_exists(ROOT / "evals" / "cases" / case_name)

    def validate_schema_contract(self) -> None:
        expected_names = [line.split(":", 1)[0] for line in EXPECTED_MARKER_LINES[1:-1]]
        if marker_field_order() != expected_names:
            self.fail("schema required[] order must match repository marker order")
        if marker_template_lines() != EXPECTED_MARKER_LINES:
            self.fail("schema-derived marker template lines must match repository marker block")
        if marker_allowed_values() != MARKER_ENUMS:
            self.fail("schema enum/const marker values must match validator constants")
        valid_blocked_expanded = {
            "HANDOFF_MODE": "expanded",
            "DETAIL_ARTIFACTS_READY": "no",
            "SAFE_FOR_NEW_SESSION": "no",
        }
        invalid_blocked_compact = {
            "HANDOFF_MODE": "compact",
            "DETAIL_ARTIFACTS_READY": "yes",
            "SAFE_FOR_NEW_SESSION": "no",
        }
        if validate_marker_semantics(valid_blocked_expanded):
            self.fail("expanded handoffs may be unsafe while detail artifacts are not ready")
        if not validate_marker_semantics(invalid_blocked_compact):
            self.fail("compact handoffs must use DETAIL_ARTIFACTS_READY=not-needed even when unsafe")

    def extract_marker_block(self, text: str, path: Path) -> list[str] | None:
        pattern = re.compile(
            rf"```text\n({MARKER_BLOCK_START}\n.*?{MARKER_BLOCK_END})\n```",
            re.DOTALL,
        )
        blocks = pattern.findall(text)
        if len(blocks) != 1:
            self.fail(
                f"{path.relative_to(ROOT)} must contain exactly one automation marker block, found {len(blocks)}"
            )
            return None
        return blocks[0].splitlines()

    def validate_marker_blocks(self) -> None:
        for path in HANDOFF_FILES:
            text = self.read(path)
            block = self.extract_marker_block(text, path)
            if block is None:
                continue
            actual_names = [line.split(":", 1)[0] for line in block]
            expected_names = [MARKER_BLOCK_START, *marker_field_order(), MARKER_BLOCK_END]
            if actual_names != expected_names:
                self.fail(f"{path.relative_to(ROOT)} marker block does not match expected field order")
            self.validate_marker_values(path, block)

        path = SKILL_DIR / "references" / "handoff-contract.md"
        text = self.read(path)
        for marker in marker_field_order():
            if marker not in text:
                self.fail(f"{path.relative_to(ROOT)} missing marker name {marker}")

    def validate_marker_values(self, path: Path, block: list[str]) -> None:
        values: dict[str, str] = {}
        for line in block:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            values[key] = value.strip()
        if any("<" in value or "|" in value for value in values.values()):
            if "references/handoff-template.md" not in path.as_posix():
                self.fail(f"{path.relative_to(ROOT)} marker block contains placeholder values")
            return
        for key, allowed in MARKER_ENUMS.items():
            value = values.get(key, "")
            if value not in allowed:
                self.fail(f"{path.relative_to(ROOT)} marker {key} has invalid value {value!r}")
        for error in validate_marker_semantics(values):
            self.fail(f"{path.relative_to(ROOT)} {error}")

    def validate_handoff_sections(self) -> None:
        required_sections = [
            "## TL;DR / Operational Summary",
            "## Recovery Contract",
            "## Session Target",
            "## Repo Snapshot",
            "## Required Reading",
            "## Change Manifest",
            "## Validation Manifest",
            "## Remaining Work",
            "## Resume Prompt",
            "## Automation Markers",
        ]
        tldr_fields = ["- Goal:", "- Current state:", "- Next action:", "- Blocker:"]
        for path in HANDOFF_FILES:
            text = self.read(path)
            for section in required_sections:
                if section not in text:
                    self.fail(f"{path.relative_to(ROOT)} missing section {section}")
            for field in tldr_fields:
                if text.count(field) != 1:
                    self.fail(f"{path.relative_to(ROOT)} must contain exactly one TL;DR field {field}")
            if "Expected drift from captured state:" not in text:
                self.fail(f"{path.relative_to(ROOT)} missing expected drift field")
            if (
                "If disk state differs" not in text
                and "If the handoff conflicts" not in text
                and "Trust order: disk/current working tree" not in text
                and "Current working tree and Git state" not in text
            ):
                self.fail(f"{path.relative_to(ROOT)} must state disk-conflict handling")
            if "SECRET_REDACTION_CHECKED: yes" in text and "Secret redaction check:" not in text:
                self.fail(f"{path.relative_to(ROOT)} records secret check yes without a check method")
            if "references/handoff-template.md" not in path.as_posix() and "HANDOFF_MODE: compact" in text:
                detail_refs = sorted(set(re.findall(r"`(details/[^`]+\.md)`", text)))
                if detail_refs:
                    self.fail(f"{path.relative_to(ROOT)} compact handoff references detail artifacts")
            if path.name == "HANDOFF.md" and "HANDOFF_READY: /" in text:
                marker_line = next(
                    (line for line in text.splitlines() if line.startswith("HANDOFF_READY: /")),
                    "",
                )
                if "references/handoff-template.md" not in path.as_posix() and ".new-session-handoff/HANDOFF.md" not in marker_line:
                    self.fail(f"{path.relative_to(ROOT)} should demonstrate the default .new-session-handoff/HANDOFF.md path")
        template = self.read(SKILL_DIR / "references" / "handoff-contract.md")
        for line in TRUST_ORDER_LINES:
            if line not in template:
                self.fail(f"handoff-contract.md missing trust order line: {line}")

    def validate_no_legacy_prompt_file_reference(self) -> None:
        legacy_prompt_file = "NEW_SESSION_PROMPT" + ".txt"
        for dirpath, dirnames, filenames in os.walk(ROOT):
            dirnames[:] = [dirname for dirname in dirnames if dirname != ".git"]
            if legacy_prompt_file in filenames:
                path = Path(dirpath) / legacy_prompt_file
                self.fail(f"{path.relative_to(ROOT)} must not exist")

        forbidden_paths = [
            ROOT / "examples" / ("resume-prompt" + ".example.txt"),
        ]
        for path in forbidden_paths:
            if path.exists():
                self.fail(f"{path.relative_to(ROOT)} must not exist")

        checked_roots = [
            ROOT / "README.md",
            ROOT / "AGENTS.md",
            ROOT / "SECURITY.md",
            ROOT / "CHANGELOG.md",
            ROOT / "examples",
            ROOT / "evals",
            ROOT / "orchestrators",
            ROOT / "scripts",
            SKILL_DIR,
        ]
        allowed_suffixes = {".json", ".md", ".py", ".txt", ".yaml", ".yml"}
        for base in checked_roots:
            paths = [base] if base.is_file() else sorted(base.rglob("*"))
            for path in paths:
                if not path.is_file() or path.suffix not in allowed_suffixes:
                    continue
                text = path.read_text(encoding="utf-8")
                if legacy_prompt_file in text:
                    self.fail(
                        f"{path.relative_to(ROOT)} must not reference legacy prompt sidecar"
                    )

    def validate_expanded_artifacts(self) -> None:
        handoff = ROOT / "examples" / "expanded-architecture" / "HANDOFF.md"
        text = self.read(handoff)
        for rel in sorted(set(re.findall(r"`(details/[^`]+\.md)`", text))):
            self.require_exists(handoff.parent / rel)

    def validate_secret_hygiene(self) -> None:
        secret_patterns = [
            r"sk-[A-Za-z0-9_-]{20,}",
            r"ghp_[A-Za-z0-9_]{20,}",
            r"(?i)(api[_-]?key|token|password|secret)\s*=\s*['\"][^'\"]+['\"]",
        ]
        checked_roots = [
            ROOT / "README.md",
            ROOT / "SECURITY.md",
            ROOT / "evals",
            ROOT / "examples",
            SKILL_DIR,
        ]
        for base in checked_roots:
            paths = [base] if base.is_file() else sorted(base.rglob("*"))
            for path in paths:
                if not path.is_file() or path.suffix not in {".json", ".md", ".txt", ".yaml"}:
                    continue
                text = path.read_text(encoding="utf-8")
                for pattern in secret_patterns:
                    if re.search(pattern, text):
                        self.fail(f"possible secret in {path.relative_to(ROOT)}")

    def run(self, checks: set[str]) -> int:
        all_checks = {
            "frontmatter": self.validate_frontmatter,
            "references": self.validate_references,
            "readme-format": self.validate_readme_format,
            "trigger-evals": self.validate_trigger_evals,
            "schema": self.validate_schema_contract,
            "markers": self.validate_marker_blocks,
            "examples": self.validate_handoff_sections,
            "expanded": self.validate_expanded_artifacts,
            "legacy-prompt-file": self.validate_no_legacy_prompt_file_reference,
            "secrets": self.validate_secret_hygiene,
        }
        selected = all_checks if "all" in checks else {k: v for k, v in all_checks.items() if k in checks}
        unknown = checks - set(all_checks) - {"all"}
        for check in sorted(unknown):
            self.fail(f"unknown check: {check}")
        for check, fn in selected.items():
            before = len(self.errors)
            fn()
            if len(self.errors) == before:
                print(f"ok: {check}")
        if self.errors:
            for error in self.errors:
                print(f"error: {error}", file=sys.stderr)
            return 1
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="append",
        default=[],
        help="Check to run: frontmatter, references, readme-format, trigger-evals, schema, markers, examples, expanded, legacy-prompt-file, secrets, all",
    )
    args = parser.parse_args()
    checks = set(args.check or ["all"])
    return Validator().run(checks)


if __name__ == "__main__":
    raise SystemExit(main())
