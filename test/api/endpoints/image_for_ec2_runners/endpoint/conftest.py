"""Pytest fixtures for image_for_ec2_runners endpoint tests."""
import os
import sys
from pathlib import Path
from typing import Any, Dict

import boto3
import pytest

# Add lib/python to path for ec2_fleet and runner_labels imports
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
LIB_DIR = REPO_ROOT / "lib" / "python"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from .helpers import get_aws_region, get_github_repo


@pytest.fixture(scope="module")
def aws_region() -> str:
    """Return the AWS region for tests."""
    return get_aws_region()


@pytest.fixture(scope="module")
def github_repo() -> str:
    """Return the GitHub repository name."""
    return get_github_repo()


@pytest.fixture(scope="module")
def config() -> Dict[str, Any]:
    """Return the test configuration dictionary."""
    return {
        'aws_region': get_aws_region(),
        'github_repo': get_github_repo(),
    }


@pytest.fixture(scope="session")
def ec2_client():
    """Create an EC2 client for the test session."""
    return boto3.client("ec2", region_name=get_aws_region())


@pytest.fixture(scope="session")
def ssm_client():
    """Create an SSM client for the test session."""
    return boto3.client("ssm", region_name=get_aws_region())


@pytest.fixture(scope="session")
def test_ami_id():
    """Return the test AMI ID from environment."""
    return os.environ.get("TEST_AMI_ID", "")
