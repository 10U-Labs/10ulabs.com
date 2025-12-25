"""Shared fixtures for api/shared/docker_repository post-deployment tests.

These fixtures are shared between integration and e2e tests.
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
