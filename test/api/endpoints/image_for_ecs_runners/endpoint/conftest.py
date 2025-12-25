"""Pytest fixtures for image_for_ecs_runners endpoint tests."""
import os
from typing import Any, Dict

import pytest
from repo_utils import REPO_ROOT
from test_fixtures import get_shared_config

from .helpers import get_api_fqdn, get_ecr_repository, get_github_repo


# Note: aws_region fixture is inherited from test/api/conftest.py -> test_fixtures.aws
# Do not redefine it here.


@pytest.fixture(scope="module")
def github_repo() -> str:
    """Return the GitHub repository name."""
    return get_github_repo()


@pytest.fixture(scope="module")
def ecr_repository() -> str:
    """Return the ECR repository name."""
    return get_ecr_repository()


@pytest.fixture(scope="module")
def config(shared_config) -> Dict[str, Any]:
    """Return the test configuration dictionary."""
    return {
        'aws_region': shared_config['aws_region'],
        'github_repo': get_github_repo(),
        'ecr_repository': get_ecr_repository(),
    }


@pytest.fixture(scope="session")
def test_image_digest():
    """Return the test image digest from environment."""
    return os.environ.get("TEST_IMAGE_DIGEST", "")
