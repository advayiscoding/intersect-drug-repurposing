"""Read credentials from the environment, falling back to a local .env file.

The .env file is Git-ignored and never printed. Real environment variables win.
"""
from __future__ import annotations

import os
from pathlib import Path


def load_env(root: Path | None = None) -> None:
    path = (root or Path(".")) / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name, value = name.strip().upper(), value.strip().strip("'\"")
        if value and not os.environ.get(name):
            os.environ[name] = value


def credential(name: str, root: Path | None = None) -> str | None:
    load_env(root)
    return os.environ.get(name) or None
