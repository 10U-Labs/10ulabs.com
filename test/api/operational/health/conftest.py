"""Pytest fixtures for health endpoint tests."""
from typing import Dict

import pytest
from repo_utils import REPO_ROOT
from test_fixtures.config import create_simple_config

# Use shared fixtures (provides logs_client, aws_region, shared_config, etc.)
pytest_plugins = ['test_fixtures.aws', 'pytest_layers']

HEALTH_SRC = REPO_ROOT / "src" / "api" / "operational" / "health"


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Create configuration fixture from terraform.tfvars and shared outputs."""
    return create_simple_config(HEALTH_SRC / "terraform.tfvars", shared_config)
