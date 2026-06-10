#!/usr/bin/env python3
"""Forward to the portable savepoint stub helper."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "skills" / "savepoint" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from create_savepoint_stub import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
