"""Pytest fixtures for simulation-soc API tests."""
from typing import Dict

import pytest
from repo_utils import REPO_ROOT
from test_fixtures.config import create_simple_config

SOC_SIMULATIONS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "soc_simulations"


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Load test configuration from terraform.tfvars and shared outputs."""
    return create_simple_config(SOC_SIMULATIONS_SRC / "terraform.tfvars", shared_config)
