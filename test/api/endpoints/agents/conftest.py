"""Pytest fixtures for agents endpoint tests."""
from typing import Dict

import pytest
from repo_utils import REPO_ROOT

AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Create configuration fixture from shared config."""
    result: Dict[str, str] = {}
    result["aws_region"] = shared_config.get("aws_region", "us-east-2")
    result["domain_name"] = shared_config.get("domain_name", "")
    return result
