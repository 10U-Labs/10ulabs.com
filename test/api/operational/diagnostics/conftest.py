"""Pytest fixtures for diagnostics endpoint tests."""
from typing import Dict

import pytest
from repo_utils import REPO_ROOT
from test_fixtures.config import create_simple_config

# Use shared fixtures (provides logs_client, aws_region, shared_config, etc.)
pytest_plugins = ['test_fixtures.aws']

DIAGNOSTICS_SRC = REPO_ROOT / "src" / "api" / "operational" / "diagnostics"


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Load configuration from terraform.tfvars and shared outputs."""
    return create_simple_config(DIAGNOSTICS_SRC / "terraform.tfvars", shared_config)
