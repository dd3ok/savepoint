#!/usr/bin/env python3
"""Validate the savepoint skill repository contract."""

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
    SKILL_DIR / "references" / "savepoint-template.md",
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
README_ALLOWED_HANDOFF_PHRASE = (
    "`savepoint` is a text/file checkpoint skill for coding agents such as Codex and Claude. It helps "
    "hand off full-context coding sessions, preserve repo/Git state, and safely resume from "
    "`.savepoint/SAVEPOINT.md` without relying on prior chat context."
)
README_KO_ALLOWED_HANDOFF_PHRASE = (
    "`savepoint`는 Codex, Claude 같은 코딩 에이전트를 위한 text/file 체크포인트 스킬입니다. "
    "컨텍스트가 다 찬 세션을 새 세션으로 인계하고, 저장소/Git 상태를 보존해 "
    "`.savepoint/SAVEPOINT.md`에서 안전하게 이어갈 수 있게 합니다."
)
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
REMOVED_SKILL_LINKS = [
    ROOT / ".agents" / "skills" / "new-session-handoff",
    ROOT / ".claude" / "skills" / "new-session-handoff",
]
REMOVED_TERM_SCAN_ROOTS = [
    ROOT / ".github",
    ROOT / ".agents",
    ROOT / ".claude",
    ROOT / "AGENTS.md",
    ROOT / "CHANGELOG.md",
    ROOT / "README.md",
    ROOT / "README.ko.md",
    ROOT / "SECURITY.md",
    ROOT / "evals",
    ROOT / "examples",
    ROOT / "orchestrators",
    ROOT / "scripts",
    SKILL_DIR,
]
REMOVED_FORBIDDEN_PATTERNS = [
    r"\bhandoff\b",
    r"HANDOFF\.md",
    r"핸드오프",
    r"legacy alias",
    r"migration-only",
    r"compatibility wrapper",
    r"new-session-handoff",
    r"\.new-session-handoff",
    r"HANDOFF_AUTOMATION",
    r"END_HANDOFF_AUTOMATION",
    r"HANDOFF_READY",
    r"HANDOFF_MODE",
    r"HANDOFF_SCHEMA_VERSION",
    r"NEW_SESSION_PROMPT_READY",
    r"SAFE_FOR_NEW_SESSION",
    r"SAVEPOINT_AUTOMATION",
    r"SAVEPOINT_SCHEMA_VERSION",
    r"SAVEPOINT_MODE:\s*(?:lightweight|verified)\b",
    r"SAVEPOINT_MODE:\s*lightweight\|verified",
    r"\blightweight\|verified\b",
    r"(?m)^- Resume Contract$",
    r"(?m)^## Resume Contract$",
    r"\bBefore implementation\b",
    r"prompt-only",
    r"compact\|expanded\|prompt-only",
    r"compact mode",
    r"expanded mode",
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

        data: dict[str, str] = {}
        for line in lines[1:end]:
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
        for term in ["explicit", "sql", "ordinary summaries", "/new", "pty"]:
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
        for ref in sorted(set(re.findall(r"`(references/[^`]+)`", skill_text))):
            self.require_exists(SKILL_DIR / ref)
        for name in CANONICAL_REFERENCES:
            self.require_exists(SKILL_DIR / "references" / name)
        self.require_exists(SKILL_DIR / "schemas" / "savepoint-v1.schema.json")
        self.require_exists(SKILL_DIR / "scripts" / "create_savepoint_stub.py")
        self.require_exists(SKILL_DIR / "scripts" / "render_savepoint.py")
        self.require_exists(ROOT / "scripts" / "create_savepoint_stub.py")
        self.require_exists(ROOT / "scripts" / "render_savepoint.py")

        required_skill_phrases = [
            "Text savepoint",
            "File savepoint",
            ".savepoint/SAVEPOINT.md",
            "SAVEPOINT_V1",
            "RESUME_READY: yes",
            "Use 300-600 tokens for simple notes",
            "800-1200 tokens by default for coding-session transfers",
            "up to 2000 tokens for complex cross-agent transfers",
            "Do not read `scripts/*.py` or `evals/*.json` during normal savepoint create/load.",
            "`no-file`, `no files`, `in-response`, or `in the response`",
            "Keep routine file savepoints compact",
            "## Load / Resume",
            "For text savepoints, do not read references unless asked.",
            "read `references/savepoint-contract.md` only for unclear marker",
            "Read `references/context-packaging.md` only for state-file/context-budget questions.",
            "For inspect-only requests, do not clean up by default.",
            "Continue only when the user requested continuation and `RESUME_READY` is `yes`",
            "For adopted generated default savepoints",
            "scripts/create_savepoint_stub.py",
            "scripts/render_savepoint.py",
        ]
        for phrase in required_skill_phrases:
            if phrase not in skill_text:
                self.fail(f"SKILL.md missing required policy: {phrase}")

        contract_text = self.read(SKILL_DIR / "references" / "savepoint-contract.md")
        for phrase in [
            ".savepoint/SAVEPOINT.md",
            "SAVEPOINT_MODE: text|file",
            "Load / Resume Contract",
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

        template_text = self.read(SKILL_DIR / "references" / "savepoint-template.md")
        for phrase in [
            "## Resume Prompt",
            "- Next-session focus:",
            "aim for 1200-1800 tokens",
            "default to 1500-2500 tokens",
            "allow 2500-4000 tokens",
            "Consult `references/savepoint-contract.md` only when marker semantics",
            "Compact defaults",
            "SAVEPOINT_MODE: text|file",
            "continue only if the user requested continuation and RESUME_READY is yes",
            "- `git diff --cached --name-status`:",
        ]:
            if phrase not in template_text:
                self.fail(f"savepoint-template.md missing phrase: {phrase}")
        context_text = self.read(SKILL_DIR / "references" / "context-packaging.md")
        for phrase in [
            "Budget guidance is advisory, not a validation rule.",
            "Path selection happens before budget",
            "explicit text/copy-paste/no-file/no files/in-response/in the response requests remain text",
            "Use 300-600 tokens for simple copy-paste summaries.",
            "Default to 800-1200 tokens for coding-agent transfers.",
            "Allow up to 2000 tokens for complex cross-agent transfers.",
            "Aim for 1200-1800 tokens for clean-state, completed, or low-risk single-change recoverable transfers.",
            "Default to 1500-2500 tokens when changes are multi-file, unresolved, risky, validation-heavy, or the working tree state is not straightforward.",
            "Allow 2500-4000 tokens for complex ops, DB, PR, CI, or multi-agent work.",
            "If top-level `SAVEPOINT.md` would exceed about 4000 tokens",
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
        if not readme_text.startswith("# Savepoint Skill"):
            self.fail("README.md must start with '# Savepoint Skill'")
        if not readme_ko_text.startswith("# Savepoint Skill"):
            self.fail("README.ko.md must start with '# Savepoint Skill'")
        for phrase in [
            README_ALLOWED_HANDOFF_PHRASE,
            "[한국어 README](README.ko.md)",
            "Create a savepoint",
            "Create a text savepoint",
            "Create a copy-paste savepoint",
            "Create a savepoint without writing files",
            "Load the savepoint",
            "Resume from SAVEPOINT.md",
            "## Use Cases",
            "Resume a coding-agent session after the context window is full.",
            "Hand off repo/Git state from one Codex or Claude session to another.",
            "Create a copy-paste Text Savepoint for a quick one-off transfer.",
            "## Why Savepoint",
            "Savepoint turns open-ended discovery, inference, and retry work from free-form handoffs",
            "For short one-off summaries, a plain summary may be cheaper",
            "Token-efficient draft helper: `skills/savepoint/scripts/create_savepoint_stub.py`",
            "skills/savepoint/references/context-packaging.md",
            "Text Savepoint",
            "File Savepoint",
            "Load / Resume Savepoint",
            "Load/resume verifies disk state before continuation or implementation.",
            "evals/trigger-queries.json",
        ]:
            if phrase not in readme_text:
                self.fail(f"README.md missing entry: {phrase}")
        for phrase in [
            README_KO_ALLOWED_HANDOFF_PHRASE,
            "[English README](README.md)",
            "세이브포인트 만들어줘",
            "File Savepoint",
            "Load / Resume Savepoint",
            "Text Savepoint",
            "## 사용 사례",
            "컨텍스트가 다 찬 코딩 에이전트 세션을 새 세션에서 이어가기",
            "Codex 또는 Claude 세션 간 저장소/Git 상태 인계하기",
            "단발성 작업을 위한 복붙용 Text Savepoint 만들기",
            "## 왜 Savepoint인가",
            "자유 형식 handoff에서 발생하는 열린 탐색, 추론, 실패 재시도 비용",
            "단발성 짧은 요약은 일반 요약이 더 저렴할 수 있습니다.",
            "토큰 절약형 초안 helper: `skills/savepoint/scripts/create_savepoint_stub.py`",
            "세이브포인트 복붙용으로 만들어줘",
            "세이브포인트 텍스트로 만들어줘",
            "세이브포인트 파일 없이 만들어줘",
            "세이브포인트 로드해줘",
            "세이브포인트 읽어줘",
            "세이브포인트 이어서 해줘",
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
        match = re.search(r'(?m)^\s*default_prompt:\s*"([^"]+)"\s*$', text)
        if not match:
            self.fail("agents/openai.yaml default_prompt must be a quoted single-line string")
            return
        prompt = match.group(1)
        for phrase in [
            "$savepoint",
            "create",
            "update",
            "inspect",
            "resume",
            "text",
            "file",
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
            self.fail("trigger evals should include no-files text savepoint requests")
        if not has_in_response_text_positive:
            self.fail("trigger evals should include in-response text savepoint requests")
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

    def validate_schema_contract(self) -> None:
        expected_names = [line.split(":", 1)[0] for line in EXPECTED_MARKER_LINES[1:-1]]
        if marker_field_order() != expected_names:
            self.fail("schema required[] order must match repository marker order")
        if marker_template_lines() != EXPECTED_MARKER_LINES:
            self.fail("schema-derived marker template lines must match repository marker block")
        if marker_allowed_values() != MARKER_ENUMS:
            self.fail("schema enum/const marker values must match validator constants")
        if not validate_marker_semantics({"SAVEPOINT_MODE": "text", "SAVEPOINT_PATH": "not-written", "DETAILS_READY": "not-needed", "RESUME_READY": "yes"}):
            self.fail("text savepoints must not be RESUME_READY=yes")
        if validate_marker_semantics({"SAVEPOINT_MODE": "file", "SAVEPOINT_PATH": "/tmp/SAVEPOINT.md", "DETAILS_READY": "no", "RESUME_READY": "no"}):
            self.fail("unsafe file savepoints may have pending detail artifacts")

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

        contract_text = self.read(SKILL_DIR / "references" / "savepoint-contract.md")
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
        contract = self.read(SKILL_DIR / "references" / "savepoint-contract.md")
        for line in TRUST_ORDER_LINES:
            if line not in contract:
                self.fail(f"savepoint-contract.md missing trust order line: {line}")

    def validate_text_example(self) -> None:
        text = self.read(TEXT_EXAMPLE)
        for phrase in [
            "# Text Savepoint Response",
            "No files were written.",
            "## Transfer Note",
            "This is not a file savepoint.",
            "Do not claim .savepoint/SAVEPOINT.md exists.",
        ]:
            if phrase not in text:
                self.fail(f"{TEXT_EXAMPLE.relative_to(ROOT)} missing text example phrase: {phrase}")
        if "SAVEPOINT_V1" in text:
            self.fail(f"{TEXT_EXAMPLE.relative_to(ROOT)} text example should omit markers by default")
        if ".savepoint/SAVEPOINT.md" in text:
            if "Do not claim .savepoint/SAVEPOINT.md exists." not in text:
                self.fail(f"{TEXT_EXAMPLE.relative_to(ROOT)} text example must not point to a missing default savepoint file")

    def validate_no_removed_prompt_file_reference(self) -> None:
        removed_prompt_file = "NEW_SESSION_PROMPT" + ".txt"
        for dirpath, dirnames, filenames in os.walk(ROOT):
            dirnames[:] = [dirname for dirname in dirnames if dirname != ".git"]
            if removed_prompt_file in filenames:
                self.fail(f"{(Path(dirpath) / removed_prompt_file).relative_to(ROOT)} must not exist")

    def validate_skill_links(self) -> None:
        for path in REMOVED_SKILL_LINKS:
            if path.exists() or path.is_symlink():
                self.fail(f"removed skill link must not exist: {path.relative_to(ROOT)}")
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

    def validate_no_removed_terms(self) -> None:
        for path in self.iter_text_paths(REMOVED_TERM_SCAN_ROOTS):
            if path == ROOT / "scripts" / "validate-repo.py":
                continue
            text = self.read_link_target(path) if path.is_symlink() else path.read_text(encoding="utf-8")
            if path == ROOT / "README.md":
                text = text.replace(README_ALLOWED_HANDOFF_PHRASE, "", 1)
            if path == ROOT / "README.ko.md":
                text = text.replace(README_KO_ALLOWED_HANDOFF_PHRASE, "", 1)
            for pattern in REMOVED_FORBIDDEN_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    self.fail(f"removed term {pattern!r} in {path.relative_to(ROOT)}")

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
            "schema": self.validate_schema_contract,
            "markers": self.validate_marker_blocks,
            "examples": self.validate_savepoint_sections,
            "text-example": self.validate_text_example,
            "detail-artifacts": self.validate_detail_artifacts,
            "removed-prompt-file": self.validate_no_removed_prompt_file_reference,
            "skill-links": self.validate_skill_links,
            "removed-terms": self.validate_no_removed_terms,
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
        help="Check to run: frontmatter, references, readme-format, agent-metadata, trigger-evals, schema, markers, examples, text-example, detail-artifacts, removed-prompt-file, skill-links, removed-terms, secrets, all",
    )
    args = parser.parse_args()
    checks = set(args.check or ["all"])
    return Validator().run(checks)


if __name__ == "__main__":
    raise SystemExit(main())
