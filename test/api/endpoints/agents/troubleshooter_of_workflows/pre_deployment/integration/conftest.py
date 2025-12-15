"""Pytest fixtures for troubleshooter_of_workflows pre-deployment integration tests.

All shared fixtures (aws_region, ssm_client, s3_client, etc.) are inherited
from test/conftest.py which parses values from the shared Terraform module.
"""

import pytest

from test.api.conftest import REPO_ROOT, terraform_init, terraform_output


AGENTS_SHARED_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "agents" / "shared"


@pytest.fixture(scope="session")
def agents_shared_terraform_initialized():
    """Initialize terraform for agents_shared state access."""
    return terraform_init(AGENTS_SHARED_DIR)


@pytest.fixture(scope="session")
def agents_shared_outputs(request):
    """Get agents_shared terraform outputs."""
    if not request.getfixturevalue("agents_shared_terraform_initialized"):
        pytest.skip("Terraform init failed for agents_shared")
    return {
        "ecr_repository_arn": terraform_output(
            AGENTS_SHARED_DIR, "ecr_repository_arn"
        ),
        "ecr_repository_name": terraform_output(
            AGENTS_SHARED_DIR, "ecr_repository_name"
        ),
        "ecr_repository_url": terraform_output(
            AGENTS_SHARED_DIR, "ecr_repository_url"
        ),
        "lambda_layer_github_auth_arn": terraform_output(
            AGENTS_SHARED_DIR, "lambda_layer_github_auth_arn"
        ),
    }
