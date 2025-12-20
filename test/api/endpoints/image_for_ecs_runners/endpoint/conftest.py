"""Pytest fixtures for image_for_ecs_runners endpoint tests."""
import os
import sys
from typing import Any, Dict

import pytest
from repo_utils import REPO_ROOT

from .helpers import get_aws_region, get_github_repo, get_ecr_repository

# Add lib/python to path for imports
LIB_DIR = REPO_ROOT / "lib" / "python"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))


@pytest.fixture(scope="session")
def aws_region() -> str:
    """Return the AWS region for tests."""
    return get_aws_region()


@pytest.fixture(scope="module")
def github_repo() -> str:
    """Return the GitHub repository name."""
    return get_github_repo()


@pytest.fixture(scope="module")
def ecr_repository() -> str:
    """Return the ECR repository name."""
    return get_ecr_repository()


@pytest.fixture(scope="module")
def config() -> Dict[str, Any]:
    """Return the test configuration dictionary."""
    return {
        'aws_region': get_aws_region(),
        'github_repo': get_github_repo(),
        'ecr_repository': get_ecr_repository(),
    }


@pytest.fixture(scope="session")
def test_image_digest():
    """Return the test image digest from environment."""
    return os.environ.get("TEST_IMAGE_DIGEST", "")
