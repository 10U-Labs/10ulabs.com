"""Shared fixtures for orchestrator unit tests."""

import sys
from pathlib import Path

import pytest


def _find_repo_root() -> Path:
    """Find the repository root by looking for .git directory."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repository root")


REPO_ROOT = _find_repo_root()

# Add src/orchestrator directory to path for imports
sys.path.insert(0, str(REPO_ROOT / "src" / "orchestrator"))
