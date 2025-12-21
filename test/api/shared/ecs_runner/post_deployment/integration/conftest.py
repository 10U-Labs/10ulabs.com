"""Pytest fixtures for api/shared/ecs_runner post-deployment integration tests.

These tests follow the 3-layer testing model from POST_DEPLOYMENT_INTEGRATION_TESTS.md:
- Layer 1: Existence - Resources were created
- Layer 2: Configuration - Resources configured correctly
- Layer 3: Wiring - Components connected properly

Layer marker system provided by pytest_layers plugin.
"""

import re

import pytest
from repo_utils import REPO_ROOT


pytest_plugins = ['pytest_layers', 'test_fixtures.aws']


SHARED_MODULE_DIR = REPO_ROOT / "lib" / "terraform" / "modules" / "shared"


@pytest.fixture(scope="module")
def expected_ecr_name():
    """Get expected ECR repository name from shared module (single source of truth)."""
    shared_outputs = (SHARED_MODULE_DIR / "outputs.tf").read_text()
    pattern = r'output "ecr_repository_name_runners"[^}]+value\s*=\s*"([^"]+)"'
    match = re.search(pattern, shared_outputs)
    if not match:
        raise ValueError("Could not find ecr_repository_name_runners in shared module")
    return match.group(1)
