#!/usr/bin/env python3
from pathlib import Path
import sys


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "english_skill_runtime.py").exists():
            return candidate
    raise SystemExit("Cannot locate english_skill_runtime.py from this skill directory.")


SKILL_DIR = Path(__file__).resolve().parents[1]
ROOT = _find_repo_root(SKILL_DIR)
sys.path.insert(0, str(ROOT))

from english_skill_runtime import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(default_skill_dir=SKILL_DIR))
