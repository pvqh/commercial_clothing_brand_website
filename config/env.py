"""Reads `KEY=value` lines from the project's `.env` file into the process environment.

Variables already set in the environment win, so production can inject them directly.
"""

import os
from pathlib import Path


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.strip().partition("=")
        if separator and not key.startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def require_env(name: str) -> str:
    try:
        return os.environ[name]
    except KeyError as missing:
        raise RuntimeError(f"Environment variable {name} is not set; see .env.example") from missing
