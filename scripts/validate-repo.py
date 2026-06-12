#!/usr/bin/env python3
"""Maintainer-only checks for savepoint repository packaging and examples.

Use the portable `validate_savepoint.py` for generated SAVEPOINT.md artifacts.
This script guards repository metadata, examples, trigger evals, marker schema,
and maintainer assets without freezing routine README/SKILL prose.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "savepoint"
SKILL_SCRIPTS = SKILL_DIR / "scripts"
SKILL_REFERENCE_DIR = SKILL_DIR / "references"
REFERENCE_DIR = ROOT / "docs" / "reference"
sys.path.insert(0, str(SKILL_SCRIPTS))

from savepoint_contract import (  # noqa: E402
    MARKER_BLOCK_END,
    MARKER_BLOCK_START,
    marker_allowed_values,
    marker_field_order,
    marker_template_lines,
    validate_marker_semantics,
)
from validate_savepoint import scan_secret_patterns  # noqa: E402

EXPECTED_MARKER_LINES = [
    "SAVEPOINT_V1",
    "SAVEPOINT_PATH: <absolute path or not-written>",
    "SAVEPOINT_MODE: text|file",
    "DETAILS_READY: yes|no|not-needed",
    "PROMPT_READY: yes|no",
    "DISK_RECORDED: yes|no",
    "VALIDATION_RECORDED: yes|no",
    "REDACTION_CHECKED: yes|no",
    "RESUME_READY: yes|no",
    "BLOCKERS: none|<short reason>",
    "END_SAVEPOINT_V1",
]
SAVEPOINT_FILES = [
    REFERENCE_DIR / "savepoint-template.md",
    ROOT / "examples" / "SAVEPOINT.filled.example.md",
    ROOT / "examples" / "file-bugfix" / "SAVEPOINT.md",
    ROOT / "examples" / "file-architecture" / "SAVEPOINT.md",
    ROOT / "examples" / "unsafe-savepoint" / "SAVEPOINT.md",
]
TEXT_EXAMPLE = ROOT / "examples" / "text-note" / "RESPONSE.md"
CANONICAL_REFERENCES = [
    "context-packaging.md",
    "savepoint-contract.md",
    "savepoint-template.md",
]
CANONICAL_SKILL_REFERENCES = [
    "contract.md",
    "safety.md",
    "template.md",
]
MARKER_ENUMS = {
    "SAVEPOINT_MODE": {"text", "file"},
    "DETAILS_READY": {"yes", "no", "not-needed"},
    "PROMPT_READY": {"yes", "no"},
    "DISK_RECORDED": {"yes", "no"},
    "VALIDATION_RECORDED": {"yes", "no"},
    "REDACTION_CHECKED": {"yes", "no"},
    "RESUME_READY": {"yes", "no"},
}
TRUST_ORDER_LINES = [
    "1. Current explicit user instruction in this session.",
    "2. Current working tree and Git state.",
    "3. Repository instruction files and durable state files such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_STATE.md`, `TASKS.md`, `DECISIONS.md`, `PLAN.md`, and `PLANS.md`.",
    "4. `SAVEPOINT.md`.",
    "5. Focused detail artifacts referenced by `SAVEPOINT.md`.",
    "6. Prior chat context only if explicitly provided by the user.",
]
KOREAN_INVOCATION_PHRASES = [
    "세이브포인트 만들어줘",
    "세이브포인트 로드해줘",
    "세이브포인트 읽어줘",
    "세이브포인트 이어서 해줘",
]
REQUIRED_TRIGGER_CASES = {
    "trigger-slash-save-01": {
        "query": "/savepoint save",
        "should_trigger": True,
        "language": "en",
        "category": "create",
    },
    "trigger-slash-load-01": {
        "query": "/savepoint load",
        "should_trigger": True,
        "language": "en",
        "category": "load",
    },
    "trigger-slash-text-01": {
        "query": "/savepoint text",
        "should_trigger": True,
        "language": "en",
        "category": "text",
    },
    "trigger-ko-resume-01": {
        "query": "세이브포인트 이어서 해줘.",
        "should_trigger": True,
        "language": "ko",
        "category": "resume",
    },
    "trigger-ko-load-01": {
        "query": "세이브포인트 로드해줘.",
        "should_trigger": True,
        "language": "ko",
        "category": "load",
    },
    "trigger-ko-read-01": {
        "query": "세이브포인트 읽어줘.",
        "should_trigger": True,
        "language": "ko",
        "category": "load",
    },
    "trigger-ko-text-direct-01": {
        "query": "세이브포인트 텍스트로 만들어줘.",
        "should_trigger": True,
        "language": "ko",
        "category": "text",
    },
    "trigger-en-load-01": {
        "query": "Load the savepoint.",
        "should_trigger": True,
        "language": "en",
        "category": "load",
    },
    "trigger-en-read-01": {
        "query": "Read the savepoint.",
        "should_trigger": True,
        "language": "en",
        "category": "load",
    },
    "trigger-en-text-direct-01": {
        "query": "Create a text savepoint.",
        "should_trigger": True,
        "language": "en",
        "category": "text",
    },
    "trigger-en-resume-01": {
        "query": "Resume from the savepoint.",
        "should_trigger": True,
        "language": "en",
        "category": "resume",
    },
    "trigger-en-compaction-recovery-01": {
        "query": "My context was automatically compacted; create a recovery savepoint so a fresh session can continue from the repo state.",
        "should_trigger": True,
        "language": "en",
        "category": "context-loss",
    },
    "trigger-en-before-new-savepoint-01": {
        "query": "Before I start a new session, create a SAVEPOINT.md with the current Git state and next action.",
        "should_trigger": True,
        "language": "en",
        "category": "create",
    },
    "no-trigger-compact-command-01": {
        "query": "Run /compact and focus on the current parser task.",
        "should_trigger": False,
        "language": "en",
        "category": "session-control",
    },
    "no-trigger-compaction-threshold-01": {
        "query": "Set the compaction threshold to 85% for this agent.",
        "should_trigger": False,
        "language": "en",
        "category": "session-control",
    },
    "no-trigger-compaction-summary-01": {
        "query": "Just summarize what happened after compaction.",
        "should_trigger": False,
        "language": "en",
        "category": "ordinary-summary",
    },
    "no-trigger-ko-sql-savepoint-01": {
        "query": "Postgres SAVEPOINT 명령 설명해줘.",
        "should_trigger": False,
        "language": "ko",
        "category": "database-savepoint",
    },
}
SKILL_LINK_TARGETS = {
    ROOT / ".agents" / "skills" / "savepoint": "../../skills/savepoint",
    ROOT / ".claude" / "skills" / "savepoint": "../../skills/savepoint",
}
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

        data: dict[str, str] = {}
        for line in lines[1:end]:
            if ":" not in line:
                self.fail(f"invalid frontmatter line: {line}")
                continue
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')

        name = data.get("name", "")
        description = data.get("description", "")
        if set(data) != {"name", "description", "argument-hint"}:
            self.fail("SKILL.md frontmatter must contain only name, description, and argument-hint")
        if name != SKILL_DIR.name:
            self.fail(f"frontmatter name must match skill directory: {name!r}")
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?", name):
            self.fail(f"frontmatter name has invalid format: {name!r}")
        if not description:
            self.fail("frontmatter description is required")
        if len(description) > 1024:
            self.fail("frontmatter description exceeds 1024 characters")
        lower_description = description.lower()
        if data.get("argument-hint") != "[save|load|text] [next-session focus]":
            self.fail("SKILL.md argument-hint must describe save/load/text and optional focus")
        for term in [
            "context reset",
            "session transfer",
            "sql",
            "ordinary summaries",
            "direct code/docs edits without checkpoint intent",
            "pty/session control",
            "session rotation",
            "/new",
            "/status",
        ]:
            if term not in lower_description:
                self.fail(f"frontmatter description must include boundary term: {term}")
        for phrase in KOREAN_INVOCATION_PHRASES:
            if phrase not in description:
                self.fail(f"frontmatter description must include Korean invocation phrase: {phrase}")
        body = "\n".join(lines[end + 1 :])
        if not body.strip().startswith("# Savepoint"):
            self.fail("SKILL.md body should start with '# Savepoint'")

    def validate_references(self) -> None:
        skill_text = self.read(SKILL_DIR / "SKILL.md")
        for name in CANONICAL_REFERENCES:
            self.require_exists(REFERENCE_DIR / name)
        for name in CANONICAL_SKILL_REFERENCES:
            self.require_exists(SKILL_REFERENCE_DIR / name)
        self.require_exists(SKILL_DIR / "schemas" / "savepoint-v1.schema.json")
        self.require_exists(SKILL_DIR / "scripts" / "savepoint.py")
        self.require_exists(SKILL_DIR / "scripts" / "render_savepoint.py")
        self.require_exists(SKILL_DIR / "scripts" / "savepoint_contract.py")
        self.require_exists(SKILL_DIR / "scripts" / "validate_savepoint.py")
        self.require_exists(ROOT / "scripts" / "savepoint.py")
        self.require_exists(ROOT / "scripts" / "render_savepoint.py")

        required_skill_phrases = [
            "Default behavior",
            "/savepoint        -> create or refresh `.savepoint/SAVEPOINT.md`",
            "/savepoint save",
            "/savepoint load",
            "/savepoint text",
            ".savepoint/SAVEPOINT.md",
            "SAVEPOINT_V1",
            "RESUME_READY: yes",
            "Do not read references, `scripts/*.py`, or `evals/*.json` during normal use.",
            "python3 <savepoint-skill-dir>/scripts/savepoint.py save",
            "append `--force` only when",
            "generated, untracked, valid default artifact",
            "`validation.project.status`",
            "`not-run-justified`",
            "`failed-expected`",
            "`no-file`, `no files`, `in-response`, or `in the response`",
            "## Load / Resume",
            "For inspect-only requests, do not clean up by default.",
            "Continue only when the user requested continuation and `RESUME_READY` is `yes`",
            "Read `references/contract.md` only when",
        ]
        for phrase in required_skill_phrases:
            if phrase not in skill_text:
                self.fail(f"SKILL.md missing required policy: {phrase}")

        contract_text = self.read(REFERENCE_DIR / "savepoint-contract.md")
        for phrase in [
            ".savepoint/SAVEPOINT.md",
            "SAVEPOINT_MODE: text|file",
            "Load / Resume Contract",
            "`/savepoint text` Contract",
            "no-file/no files, in-response/in the response",
            "Detail Spillover",
            "Do not delete tracked files",
            "Durable state files are not generated detail artifacts",
            "cleanup happens only after adoption",
            "Continue only when the user requested continuation and `RESUME_READY` is `yes`",
            "`git diff --cached --name-status`",
            "SAVEPOINT_V1",
            "required shape describes recovery facts, not prose volume",
            "After an adopted generated default savepoint has been used for continuation",
            "Default path plus untracked status is not enough to prove generated authorship",
            "Never overwrite tracked, user-authored, external-path, inspect-only, stale, unsafe, conflicting, or debug-needed savepoints.",
            "When preserving a savepoint with generated details, keep the referenced detail files in the same relative layout or update the preserved savepoint references.",
        ]:
            if phrase not in contract_text:
                self.fail(f"savepoint-contract.md missing policy phrase: {phrase}")

        template_text = self.read(REFERENCE_DIR / "savepoint-template.md")
        for phrase in [
            "## Resume Prompt",
            "- Next-session focus:",
            "Consult `docs/reference/savepoint-contract.md` only when marker semantics",
            "Compact defaults",
            "SAVEPOINT_MODE: text|file",
            "continue only if the user requested continuation and RESUME_READY is yes",
            "- `git diff --cached --name-status`:",
        ]:
            if phrase not in template_text:
                self.fail(f"savepoint-template.md missing phrase: {phrase}")
        skill_template_text = self.read(SKILL_REFERENCE_DIR / "template.md")
        marker_index = skill_template_text.find("END_SAVEPOINT_V1")
        closing_index = skill_template_text.rfind("```\n````")
        if marker_index == -1 or closing_index == -1 or closing_index < marker_index:
            self.fail("skills/savepoint/references/template.md must keep the SAVEPOINT_V1 marker inside the copyable template fence")
        context_text = self.read(REFERENCE_DIR / "context-packaging.md")
        for phrase in [
            "Budget guidance is advisory, not a validation rule.",
            "Path selection happens before budget",
            "explicit text/copy-paste/no-file/no files/in-response/in the response requests remain text",
            "Do not read `scripts/*.py` or `evals/*.json` during normal savepoint create/load.",
            "The top-level `SAVEPOINT.md` must still contain required markers",
            "repo-relative paths for files under the recorded Git root",
            "Savepoints are current recovery artifacts, not history logs.",
            "## Minimal Load Path",
            "Read details only when the listed next step or a mismatch requires them.",
        ]:
            if phrase not in context_text:
                self.fail(f"context-packaging.md missing phrase: {phrase}")

    def validate_readme_format(self) -> None:
        readme_text = self.read(ROOT / "README.md")
        readme_ko_text = self.read(ROOT / "README.ko.md")
        if readme_text.strip().startswith('"""') or readme_text.strip().endswith('"""'):
            self.fail("README.md must not be wrapped in triple quotes")
        if not readme_text.startswith("# Savepoint\n"):
            self.fail("README.md must start with '# Savepoint'")
        if not readme_ko_text.startswith("# Savepoint\n"):
            self.fail("README.ko.md must start with '# Savepoint'")
        for phrase in [
            "/savepoint save",
            "/savepoint load",
            "/savepoint text",
            "30-second usage",
            "What it guarantees",
            "What it does not guarantee",
            "Savepoint",
            ".savepoint/SAVEPOINT.md",
            "scripts/savepoint.py",
            "scripts/validate-repo.py",
            "python3 -m compileall",
        ]:
            if phrase not in readme_text:
                self.fail(f"README.md missing entry: {phrase}")
        for phrase in [
            "/savepoint save",
            "/savepoint load",
            "/savepoint text",
            "30초 사용법",
            "보장하는 것",
            "보장하지 않는 것",
            "Savepoint",
            ".savepoint/SAVEPOINT.md",
            "scripts/savepoint.py",
            "scripts/validate-repo.py",
            "python3 -m compileall",
        ]:
            if phrase not in readme_ko_text:
                self.fail(f"README.ko.md missing entry: {phrase}")

    def validate_agent_metadata(self) -> None:
        path = SKILL_DIR / "agents" / "openai.yaml"
        text = self.read(path)
        for phrase in [
            'display_name: "Savepoint"',
            "short_description:",
            "default_prompt:",
        ]:
            if phrase not in text:
                self.fail(f"agents/openai.yaml missing phrase: {phrase}")
        if "allow_implicit_invocation:" in text and "allow_implicit_invocation: true" not in text:
            self.fail("agents/openai.yaml allow_implicit_invocation must be true when present")
        match = re.search(r'(?m)^\s*default_prompt:\s*"([^"]+)"\s*$', text)
        if not match:
            self.fail("agents/openai.yaml default_prompt must be a quoted single-line string")
            return
        prompt = match.group(1)
        for phrase in [
            "$savepoint",
            "create",
            "load",
            "verify",
            "text",
            "copy-paste",
            ".savepoint/SAVEPOINT.md",
        ]:
            if phrase not in prompt:
                self.fail(f"agents/openai.yaml default_prompt missing phrase: {phrase}")

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
        if data.get("skill_name") != "savepoint":
            self.fail("evals/trigger-queries.json skill_name must be savepoint")
        if data.get("version") != 1:
            self.fail("evals/trigger-queries.json version must be 1")
        if not isinstance(queries, list):
            self.fail("evals/trigger-queries.json queries must be a list")
            return
        if len(queries) < 16:
            self.fail("evals/trigger-queries.json should contain at least 16 trigger queries")

        required_fields = {"id", "query", "should_trigger", "language", "category", "rationale"}
        seen_ids: set[str] = set()
        seen_required_trigger_cases: set[str] = set()
        positives = negatives = 0
        has_korean_positive = False
        has_korean_negative = False
        has_secret_positive = False
        has_focus_positive = False
        has_short_file_positive = False
        has_no_files_text_positive = False
        has_in_response_text_positive = False
        has_korean_load_positive = False
        has_english_load_positive = False
        has_korean_read_positive = False
        has_korean_start_positive = False
        has_english_read_positive = False
        has_english_start_positive = False
        has_sql_negative = False
        has_korean_sql_negative = False
        negative_categories: set[str] = set()
        for index, query in enumerate(queries):
            if not isinstance(query, dict):
                self.fail(f"trigger eval query #{index} must be an object")
                continue
            missing = required_fields - set(query)
            if missing:
                self.fail(f"trigger eval query #{index} missing fields: {sorted(missing)}")
            query_id = query.get("id")
            query_text = query.get("query")
            category = query.get("category")
            if not isinstance(query_id, str) or not query_id.strip():
                self.fail(f"trigger eval query #{index} has invalid id")
            elif query_id in seen_ids:
                self.fail(f"evals/trigger-queries.json contains duplicate id: {query_id}")
            else:
                seen_ids.add(query_id)
            if not isinstance(query_text, str) or not query_text.strip():
                self.fail(f"trigger eval query #{index} has empty query")
            if isinstance(query_id, str) and query_id in REQUIRED_TRIGGER_CASES:
                expected = REQUIRED_TRIGGER_CASES[query_id]
                mismatches = [
                    key
                    for key, value in expected.items()
                    if query.get(key) != value
                ]
                if mismatches:
                    self.fail(
                        f"trigger eval {query_id} has mismatched fields: {mismatches}"
                    )
                else:
                    seen_required_trigger_cases.add(query_id)
            should_trigger = query.get("should_trigger")
            if should_trigger is True:
                positives += 1
                if isinstance(query_text, str) and "세이브포인트" in query_text:
                    has_korean_positive = True
                if category == "secret-redaction":
                    has_secret_positive = True
                if category == "focus-argument":
                    has_focus_positive = True
                if query_id == "trigger-ko-file-short-01":
                    has_short_file_positive = True
                if category == "text" and isinstance(query_text, str) and "no files" in query_text.lower():
                    has_no_files_text_positive = True
                if category == "text" and isinstance(query_text, str) and "in the response" in query_text.lower():
                    has_in_response_text_positive = True
                if category == "load" and query.get("language") == "ko":
                    has_korean_load_positive = True
                if category == "load" and query.get("language") == "en":
                    has_english_load_positive = True
                if query_id == "trigger-ko-read-01":
                    has_korean_read_positive = True
                if query_id == "trigger-ko-resume-01":
                    has_korean_start_positive = True
                if query_id == "trigger-en-read-01":
                    has_english_read_positive = True
                if query_id == "trigger-en-resume-01":
                    has_english_start_positive = True
            elif should_trigger is False:
                negatives += 1
                if query.get("language") == "ko":
                    has_korean_negative = True
                if isinstance(category, str):
                    negative_categories.add(category)
                    if category == "database-savepoint":
                        has_sql_negative = True
                        if query.get("language") == "ko":
                            has_korean_sql_negative = True
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
        if not has_korean_positive:
            self.fail("trigger evals should include Korean savepoint trigger queries")
        if not has_korean_negative:
            self.fail("trigger evals should include Korean near-miss negative queries")
        if not has_secret_positive:
            self.fail("trigger evals should include secret-bearing savepoint requests")
        if not has_focus_positive:
            self.fail("trigger evals should include next-session focus savepoint requests")
        if not has_short_file_positive:
            self.fail("trigger evals should include short generic savepoint requests that still default to file")
        if not has_no_files_text_positive:
            self.fail("trigger evals should include no-files /savepoint text requests")
        if not has_in_response_text_positive:
            self.fail("trigger evals should include in-response /savepoint text requests")
        if not has_korean_load_positive:
            self.fail("trigger evals should include Korean load-only savepoint requests")
        if not has_english_load_positive:
            self.fail("trigger evals should include English load-only savepoint requests")
        if not has_korean_read_positive:
            self.fail("trigger evals should include Korean read-only savepoint requests")
        if not has_korean_start_positive:
            self.fail("trigger evals should include Korean resume-from-savepoint requests")
        if not has_english_read_positive:
            self.fail("trigger evals should include English read-only savepoint requests")
        if not has_english_start_positive:
            self.fail("trigger evals should include English resume-from-savepoint requests")
        if not has_sql_negative:
            self.fail("trigger evals should include database/SQL SAVEPOINT negative queries")
        if not has_korean_sql_negative:
            self.fail("trigger evals should include Korean database/SQL SAVEPOINT negative queries")
        missing_required_cases = set(REQUIRED_TRIGGER_CASES) - seen_required_trigger_cases
        if missing_required_cases:
            self.fail(f"trigger evals missing required exact cases: {sorted(missing_required_cases)}")

        required_negative_categories = {
            "ordinary-summary",
            "repo-instructions",
            "implementation",
            "session-control",
            "status-command",
            "state-file-authoring",
            "database-savepoint",
        }
        missing = required_negative_categories - negative_categories
        if missing:
            self.fail(f"trigger evals missing near-miss negative categories: {sorted(missing)}")

    def validate_manual_eval_cases(self) -> None:
        required_phrases = {
            ROOT / "evals" / "README.md": [
                "compaction",
                "session reset",
                "working tree",
                "Unrelated dirty files",
                "resume-ready semantics",
            ],
            ROOT / "evals" / "cases" / "resume-conflicting-disk.md": [
                "automatic context compaction",
                "`src/session.ts` is unrelated dirty work",
                "stale state",
                "prior chat",
            ],
        }
        for path, phrases in required_phrases.items():
            text = self.read(path)
            if not text:
                continue
            for phrase in phrases:
                if phrase not in text:
                    self.fail(f"{path.relative_to(ROOT)} missing eval phrase: {phrase}")
        output_contract = ROOT / "evals" / "output-contract.json"
        self.require_exists(output_contract)
        if not output_contract.exists():
            return
        try:
            data = json.loads(output_contract.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.fail(f"evals/output-contract.json is invalid JSON: {exc}")
            return
        categories = {case.get("category") for case in data.get("cases", []) if isinstance(case, dict)}
        for category in [
            "artifact-contract",
            "security-redaction",
            "resume-ready-semantics",
            "token-budget",
            "no-unwanted-files",
            "least-permission",
        ]:
            if category not in categories:
                self.fail(f"evals/output-contract.json missing category: {category}")

    def validate_schema_contract(self) -> None:
        expected_names = [line.split(":", 1)[0] for line in EXPECTED_MARKER_LINES[1:-1]]
        if marker_field_order() != expected_names:
            self.fail("schema required[] order must match repository marker order")
        if marker_template_lines() != EXPECTED_MARKER_LINES:
            self.fail("schema-derived marker template lines must match repository marker block")
        if marker_allowed_values() != MARKER_ENUMS:
            self.fail("schema enum/const marker values must match validator constants")
        if not validate_marker_semantics({"SAVEPOINT_MODE": "text", "SAVEPOINT_PATH": "not-written", "DETAILS_READY": "not-needed", "RESUME_READY": "yes"}):
            self.fail("/savepoint text outputs must not be RESUME_READY=yes")
        if validate_marker_semantics({"SAVEPOINT_MODE": "file", "SAVEPOINT_PATH": "/tmp/SAVEPOINT.md", "DETAILS_READY": "no", "RESUME_READY": "no"}):
            self.fail("unsafe Savepoints may have pending detail artifacts")

    def extract_marker_block(self, text: str, path: Path) -> list[str] | None:
        pattern = re.compile(
            rf"```text\r?\n({MARKER_BLOCK_START}\r?\n.*?{MARKER_BLOCK_END})\r?\n```",
            re.DOTALL,
        )
        blocks = pattern.findall(text)
        if len(blocks) != 1:
            self.fail(f"{path.relative_to(ROOT)} must contain exactly one marker block, found {len(blocks)}")
            return None
        return blocks[0].splitlines()

    def validate_marker_blocks(self) -> None:
        for path in SAVEPOINT_FILES:
            text = self.read(path)
            block = self.extract_marker_block(text, path)
            if block is None:
                continue
            actual_names = [line.split(":", 1)[0] for line in block]
            expected_names = [MARKER_BLOCK_START, *marker_field_order(), MARKER_BLOCK_END]
            if actual_names != expected_names:
                self.fail(f"{path.relative_to(ROOT)} marker block does not match expected field order")
            self.validate_marker_values(path, block)

        contract_text = self.read(REFERENCE_DIR / "savepoint-contract.md")
        for marker in marker_field_order():
            if marker not in contract_text:
                self.fail(f"savepoint-contract.md missing marker name {marker}")

    def validate_marker_values(self, path: Path, block: list[str]) -> None:
        values: dict[str, str] = {}
        for line in block:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            values[key] = value.strip()
        if any("<" in value or "|" in value for value in values.values()):
            if "savepoint-template.md" not in path.as_posix():
                self.fail(f"{path.relative_to(ROOT)} marker block contains placeholder values")
            return
        for key, allowed in MARKER_ENUMS.items():
            value = values.get(key, "")
            if value not in allowed:
                self.fail(f"{path.relative_to(ROOT)} marker {key} has invalid value {value!r}")
        for error in validate_marker_semantics(values):
            self.fail(f"{path.relative_to(ROOT)} {error}")

    def validate_savepoint_sections(self) -> None:
        required_sections = [
            "## TL;DR / Operational Summary",
            "## Repo Snapshot",
            "## Required Reading",
            "## Change Manifest",
            "## Recovery Notes",
            "## Validation Manifest",
            "## Resume Prompt",
            "## Markers",
        ]
        tldr_fields = ["- Goal:", "- Current state:", "- Next action:", "- Blocker:"]
        for path in SAVEPOINT_FILES:
            text = self.read(path)
            for section in required_sections:
                if section not in text:
                    self.fail(f"{path.relative_to(ROOT)} missing section {section}")
            for field in tldr_fields:
                if text.count(field) != 1:
                    self.fail(f"{path.relative_to(ROOT)} must contain exactly one TL;DR field {field}")
            if "Expected drift from captured state:" not in text:
                self.fail(f"{path.relative_to(ROOT)} missing expected drift field")
            if "- `git diff --cached --name-status`:" not in text:
                self.fail(f"{path.relative_to(ROOT)} missing staged name-status field")
            if "SAVEPOINT_MODE: file" in text and "SAVEPOINT_PATH: /" in text:
                marker_line = next((line for line in text.splitlines() if line.startswith("SAVEPOINT_PATH: /")), "")
                if "savepoint-template.md" not in path.as_posix() and ".savepoint/SAVEPOINT.md" not in marker_line:
                    self.fail(f"{path.relative_to(ROOT)} should demonstrate the default .savepoint/SAVEPOINT.md path")
        contract = self.read(REFERENCE_DIR / "savepoint-contract.md")
        for line in TRUST_ORDER_LINES:
            if line not in contract:
                self.fail(f"savepoint-contract.md missing trust order line: {line}")

    def validate_text_example(self) -> None:
        text = self.read(TEXT_EXAMPLE)
        for phrase in [
            "No files were written.",
            "Do not claim .savepoint/SAVEPOINT.md exists.",
        ]:
            if phrase not in text:
                self.fail(f"{TEXT_EXAMPLE.relative_to(ROOT)} missing text example phrase: {phrase}")
        if "SAVEPOINT_V1" in text:
            self.fail(f"{TEXT_EXAMPLE.relative_to(ROOT)} text example should omit markers by default")
        if ".savepoint/SAVEPOINT.md" in text:
            if "Do not claim .savepoint/SAVEPOINT.md exists." not in text:
                self.fail(f"{TEXT_EXAMPLE.relative_to(ROOT)} text example must not point to a missing default savepoint file")

    def validate_skill_links(self) -> None:
        for path, expected_target in SKILL_LINK_TARGETS.items():
            if not path.exists() and not path.is_symlink():
                self.fail(f"missing savepoint skill link: {path.relative_to(ROOT)}")
                continue
            actual_target = self.read_link_target(path)
            if actual_target != expected_target:
                self.fail(
                    f"{path.relative_to(ROOT)} must point to {expected_target!r}, "
                    f"got {actual_target!r}"
                )
            blob_target = self.read_git_link_blob(path)
            if blob_target is not None and blob_target != expected_target:
                self.fail(
                    f"{path.relative_to(ROOT)} committed link target must be "
                    f"{expected_target!r}, got {blob_target!r}"
                )

    def read_link_target(self, path: Path) -> str:
        if path.is_symlink():
            return os.readlink(path).replace("\\", "/")
        if path.is_file():
            return path.read_text(encoding="utf-8").replace("\\", "/")
        return ""

    def read_git_link_blob(self, path: Path) -> str | None:
        relative = path.relative_to(ROOT).as_posix()
        try:
            mode = subprocess.check_output(
                ["git", "ls-files", "-s", "--", relative],
                cwd=ROOT,
                text=True,
                stderr=subprocess.DEVNULL,
            ).split(maxsplit=1)[0]
        except (subprocess.CalledProcessError, IndexError, FileNotFoundError):
            return None
        if mode != "120000":
            return None
        try:
            return subprocess.check_output(
                ["git", "cat-file", "-p", f":{relative}"],
                cwd=ROOT,
                text=True,
                stderr=subprocess.DEVNULL,
            ).replace("\\", "/")
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def iter_text_paths(self, roots: list[Path]) -> list[Path]:
        paths: list[Path] = []
        for root in roots:
            if not root.exists() and not root.is_symlink():
                continue
            candidates = [root] if root.is_file() or root.is_symlink() else sorted(root.rglob("*"))
            for path in candidates:
                if path.is_dir() and not path.is_symlink():
                    continue
                if "__pycache__" in path.parts:
                    continue
                if path.suffix in {".md", ".py", ".json", ".yaml", ".yml", ".txt"} or not path.suffix:
                    paths.append(path)
        return paths

    def validate_detail_artifacts(self) -> None:
        savepoint = ROOT / "examples" / "file-architecture" / "SAVEPOINT.md"
        text = self.read(savepoint)
        for rel in sorted(set(re.findall(r"`(details/[^`]+\.md)`", text))):
            self.require_exists(savepoint.parent / rel)

    def validate_secret_hygiene(self) -> None:
        checked_roots = [
            ROOT / ".github",
            ROOT / ".agents",
            ROOT / ".claude",
            ROOT / "AGENTS.md",
            ROOT / "CHANGELOG.md",
            ROOT / "README.md",
            ROOT / "SECURITY.md",
            ROOT / "evals",
            ROOT / "examples",
            ROOT / "docs",
            ROOT / "orchestrators",
            SKILL_DIR,
        ]
        for base in checked_roots:
            paths = [base] if base.is_file() else sorted(base.rglob("*"))
            for path in paths:
                if not path.is_file() or path.suffix not in {".json", ".md", ".txt", ".yaml"}:
                    continue
                text = path.read_text(encoding="utf-8")
                secret_errors: list[str] = []
                scan_secret_patterns(path.relative_to(ROOT), text, secret_errors)
                for error in secret_errors:
                    self.fail(error)

    def run(self, checks: set[str]) -> int:
        all_checks = {
            "frontmatter": self.validate_frontmatter,
            "references": self.validate_references,
            "readme-format": self.validate_readme_format,
            "agent-metadata": self.validate_agent_metadata,
            "trigger-evals": self.validate_trigger_evals,
            "manual-evals": self.validate_manual_eval_cases,
            "schema": self.validate_schema_contract,
            "markers": self.validate_marker_blocks,
            "examples": self.validate_savepoint_sections,
            "text-example": self.validate_text_example,
            "detail-artifacts": self.validate_detail_artifacts,
            "skill-links": self.validate_skill_links,
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
        help="Check to run: frontmatter, references, readme-format, agent-metadata, trigger-evals, manual-evals, schema, markers, examples, text-example, detail-artifacts, skill-links, secrets, all",
    )
    args = parser.parse_args()
    checks = set(args.check or ["all"])
    return Validator().run(checks)


if __name__ == "__main__":
    raise SystemExit(main())
