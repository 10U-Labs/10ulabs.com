"""Pytest fixtures for agents post-deployment integration tests."""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"
