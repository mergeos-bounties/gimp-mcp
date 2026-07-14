from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

Mode = Literal["mock", "live"]
_PREFIX = "GIMP_MCP"


def get_mode() -> Mode:
    raw = (os.environ.get(f"{_PREFIX}_MODE") or "mock").strip().lower()
    return "live" if raw == "live" else "mock"


def set_mode(mode: str) -> Mode:
    m: Mode = "live" if mode.strip().lower() == "live" else "mock"
    os.environ[f"{_PREFIX}_MODE"] = m
    return m


def gimp_bin() -> str | None:
    """Override path to gimp-console executable."""
    v = (os.environ.get(f"{_PREFIX}_BIN") or os.environ.get("GIMP_CONSOLE") or "").strip()
    return v or None


def workspace_dir() -> Path:
    raw = (os.environ.get(f"{_PREFIX}_WORKSPACE") or "").strip()
    if raw:
        p = Path(raw)
    else:
        p = Path.home() / ".gimp-mcp" / "workspace"
    p.mkdir(parents=True, exist_ok=True)
    return p


def batch_timeout_sec() -> float:
    try:
        return float(os.environ.get(f"{_PREFIX}_TIMEOUT") or "120")
    except ValueError:
        return 120.0
