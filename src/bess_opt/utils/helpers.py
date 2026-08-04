"""Small shared helpers: config loading, time indexing, path resolution."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_yaml(path: str | Path) -> Dict[str, Any]:
    full_path = resolve_path(path)
    with open(full_path, "r") as f:
        return yaml.safe_load(f)


def resolve_path(path: str | Path) -> Path:
    """Resolve a path relative to the project root if it isn't already absolute."""
    p = Path(path)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


def build_time_index(start: str, hours: int, timestep_minutes: int) -> list[datetime]:
    start_dt = datetime.fromisoformat(start)
    n_steps = int(hours * 60 / timestep_minutes)
    return [start_dt + timedelta(minutes=timestep_minutes * i) for i in range(n_steps)]


def ensure_dir(path: str | Path) -> Path:
    p = resolve_path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
