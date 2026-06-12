# Savepoint

Savepoint creates or verifies a recoverable coding-session checkpoint so a fresh agent can continue from current repo/Git state without prior chat context.

Savepoint is not a lightweight conversation summary. It is a recoverable repo/Git checkpoint; use `/savepoint text` or an ordinary summary when file recovery is unnecessary.

## 30-second usage

```text
/savepoint        Create or refresh .savepoint/SAVEPOINT.md.
/savepoint save   Same as default.
/savepoint load   Verify an existing savepoint and report whether continuation is safe.
/savepoint text   Print a copy-paste handoff only; no file recovery guarantee.
```

If a client does not pass custom slash prompts through, use the natural-language equivalent: `Use $savepoint to save`, `Use $savepoint to load`, or `Use $savepoint to create a text handoff`.

[Korean README](README.ko.md)

## When to use

- The context window is full or likely to compact.
- You are about to reset or transfer a coding-agent session.
- A multi-file refactor needs a verifiable resume point.
- Codex, Claude, Gemini, or an external orchestrator must hand off repo state.

## When not to use

- A short ordinary summary is enough.
- The user asks about SQL `SAVEPOINT`.
- The request is only `/status`, `/new`, compaction policy, PTY control, or session rotation.
- The user asks for direct code/docs edits without checkpoint intent, or an app feature named savepoint.
- Git commit, stash, or branch history is the right tool.

## What it guarantees

- File mode writes `.savepoint/SAVEPOINT.md`.
- The artifact includes a repo/Git snapshot, `## Resume Prompt`, and one final `SAVEPOINT_V1` marker block.
- Generated artifacts are scanned for secret-like values before `REDACTION_CHECKED: yes`.
- The bundled validator checks marker shape and safe-resume fields.
- On load, current disk state wins over savepoint text.

## What it does not guarantee

- Tests pass.
- The code is correct.
- The task is complete.
- Future conflicts are impossible.
- Repo recovery from text mode.

## Minimal CLI workflow

The portable skill entrypoint is `skills/savepoint/scripts/savepoint.py`; repository-local commands use `scripts/savepoint.py`.

`inspect --json` exits `0` when the file and marker are valid, `1` when a savepoint-like file is parsed but invalid, and `2` when the file cannot be read or is not a savepoint artifact.

Minimal file workflow:

```bash
python3 scripts/savepoint.py init-input --output .savepoint/input.json
$EDITOR .savepoint/input.json
python3 scripts/savepoint.py save --input .savepoint/input.json --output .savepoint/SAVEPOINT.md --assert-no-active-commands --scan-redaction --validate
python3 scripts/savepoint.py inspect .savepoint/SAVEPOINT.md --json
```

Use `validation.project.status` values `passed`, `failed-expected`, `failed-blocking`, `not-run-justified`, or `not-run-unknown`. With `--scan-redaction`, the input JSON is scanned before rendering; do not put raw secrets in `.savepoint/input.json`.

## Install

Recommended commands:

```bash
# Claude user install
python3 scripts/install.py --target claude --scope user --apply

# Codex repo install
python3 scripts/install.py --target codex --scope repo --apply --add-gitignore
```

The helper defaults to dry-run. It writes files only with `--apply`. With repo-scope install, `--add-gitignore` appends `.savepoint/`.

On Windows, prefer the install helper or a normal Git clone/worktree. Archive extraction tools can mishandle symlinks.

## Runtime boundary

Normal create/load should use only:

- `skills/savepoint/SKILL.md`
- `skills/savepoint/scripts/savepoint.py`
- `skills/savepoint/references/*.md` only for advanced edge cases
- `skills/savepoint/schemas/savepoint-v1.schema.json` only when debugging marker schema

Examples, evals, maintainer docs, and repository validation scripts are not normal agent context.

## Examples

- `examples/file-bugfix/`: small file savepoint.
- `examples/file-architecture/`: savepoint with focused `details/*.md` spillover.
- `examples/text-note/`: response-only `/savepoint text` note.
- `examples/unsafe-savepoint/`: intentionally unsafe `RESUME_READY: no` artifact.

## Maintainer docs

Use `scripts/savepoint.py validate .savepoint/SAVEPOINT.md` for generated artifacts.

- Repository change validation: `AGENTS.md`.
- Marker and safe-resume semantics: `docs/reference/savepoint-contract.md`.
- Compact packaging guidance: `docs/reference/context-packaging.md`.
- Manual artifact fallback: `docs/reference/savepoint-template.md`.

## Orchestrators

External PTY controllers may parse the final `SAVEPOINT_V1` block and decide whether to rotate sessions. This skill only prepares file artifacts or text notes; orchestration remains outside the skill.

See `orchestrators/session-rotation.md`.
