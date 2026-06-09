#!/usr/bin/env python3
"""Safely preview or install the new-session-handoff skill."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "new-session-handoff"
DEFAULT_SKILL_SOURCE = ROOT / "skills" / SKILL_NAME
GITIGNORE_ENTRY = ".new-session-handoff/"
IGNORED_NAMES = {"__pycache__", ".pytest_cache"}


def resolve_destination(target: str, scope: str, *, repo_root: Path, home: Path) -> Path:
    if target == "codex":
        base = Path(".agents") / "skills"
    elif target == "claude":
        base = Path(".claude") / "skills"
    else:
        raise ValueError(f"unsupported target: {target}")

    if scope == "repo":
        return repo_root / base / SKILL_NAME
    if scope == "user":
        return home / base / SKILL_NAME
    raise ValueError(f"unsupported scope: {scope}")


def iter_files(path: Path) -> list[Path]:
    return sorted(
        file
        for file in path.rglob("*")
        if file.is_file()
        and not file.name.endswith(".pyc")
        and not any(part in IGNORED_NAMES for part in file.relative_to(path).parts)
    )


def ignore_names(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in IGNORED_NAMES or name.endswith(".pyc")}


def validate_source(source: Path) -> None:
    if not source.exists() or not source.is_dir():
        raise ValueError(f"Skill source does not exist: {source}")
    if not (source / "SKILL.md").exists():
        raise ValueError(f"Skill source is missing SKILL.md: {source}")


def validate_repo_root(repo_root: Path) -> None:
    if not repo_root.exists() or not repo_root.is_dir():
        raise ValueError(f"repo root does not exist: {repo_root}")


def destination_is_occupied(destination: Path) -> bool:
    return destination.exists() or destination.is_symlink()


def append_gitignore(repo_root: Path) -> bool:
    gitignore = repo_root / ".gitignore"
    if gitignore.exists():
        with gitignore.open("r", encoding="utf-8", newline="") as handle:
            existing = handle.read()
    else:
        existing = ""

    lines = existing.splitlines()
    if GITIGNORE_ENTRY in lines:
        return False

    newline = "\r\n" if "\r\n" in existing else "\n"
    prefix = "" if not existing or existing.endswith(("\n", "\r\n")) else newline
    with gitignore.open("w", encoding="utf-8", newline="") as handle:
        handle.write(f"{existing}{prefix}{GITIGNORE_ENTRY}{newline}")
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=["claude", "codex"], required=True)
    parser.add_argument("--scope", choices=["user", "repo"], required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--skill-source", type=Path, default=DEFAULT_SKILL_SOURCE)
    parser.add_argument("--add-gitignore", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.apply and args.dry_run:
        parser.error("--apply and --dry-run cannot be used together")
    if args.add_gitignore and args.scope != "repo":
        parser.error("--add-gitignore is only valid with --scope repo")

    source = args.skill_source.resolve()
    repo_root = args.repo_root.resolve()
    home = Path.home().resolve()
    dry_run = not args.apply

    try:
        validate_source(source)
        if args.scope == "repo":
            validate_repo_root(repo_root)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    destination = resolve_destination(args.target, args.scope, repo_root=repo_root, home=home)
    if destination_is_occupied(destination):
        print("error: Destination already exists. Delete it manually before installing.", file=sys.stderr)
        print(f"Destination: {destination}", file=sys.stderr)
        return 1

    files = iter_files(source)
    target_label = f"{args.target.capitalize()} {args.scope} skill"
    print(f"Install target: {target_label}")
    print(f"Source: {source}")
    print(f"Destination: {destination}")
    print("Method: copy")
    print(f"Dry run: {'yes' if dry_run else 'no'}")
    print()

    if dry_run:
        print("Would create:")
        for file in files:
            print(f"- {destination / file.relative_to(source)}")
        if args.add_gitignore:
            print(f"Would append to {repo_root / '.gitignore'}:")
            print(f"- {GITIGNORE_ENTRY}")
        print()
        print("No files changed. Re-run with --apply to install.")
        return 0

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, ignore=ignore_names)
    gitignore_changed = append_gitignore(repo_root) if args.add_gitignore else False

    print(f"Installed {SKILL_NAME} skill:")
    print(f"- Destination: {destination}")
    print("- Method: copy")
    print(f"- Files written: {len(files)}")
    print("- Existing files overwritten: no")
    if args.add_gitignore:
        print(f"- .gitignore updated: {'yes' if gitignore_changed else 'already-present'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
