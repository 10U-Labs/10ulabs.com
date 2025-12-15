"""Pytest fixtures for agents endpoint tests."""
from pathlib import Path
from typing import Dict

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Create configuration fixture from shared config."""
    result: Dict[str, str] = {}
    result["aws_region"] = shared_config.get("aws_region", "us-east-2")
    result["domain_name"] = shared_config.get("domain_name", "")
    return result
