"""Integration test fixtures for api/common/parameters pre-deployment tests.

These tests follow the 7-layer testing model from PRE_DEPLOYMENT_INTEGRATION_TESTS.md.
"""
from repo_utils import REPO_ROOT
from test_fixtures.terraform import terraform_init

import boto3
import pytest

PARAMETERS_SRC = REPO_ROOT / "src" / "api" / "common" / "parameters"


@pytest.fixture(scope="session")
def parameters_terraform_initialized():
    """Initialize terraform for parameters state access."""
    return terraform_init(PARAMETERS_SRC)


@pytest.fixture(scope="session")
def ssm_client(aws_region):
    """Create an SSM client."""
    return boto3.client("ssm", region_name=aws_region)
