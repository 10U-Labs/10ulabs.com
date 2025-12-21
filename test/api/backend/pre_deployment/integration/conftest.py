"""Pytest fixtures for api_backend pre-deployment integration tests."""

import re

from test.api.conftest import REPO_ROOT, terraform_init, terraform_output

import pytest

# Import AWS fixtures and layer-based test dependency tracking
pytest_plugins = ['test_fixtures.aws', 'pytest_layers']


BOOTSTRAP_DIR = REPO_ROOT / "src" / "bootstrap"


@pytest.fixture(scope="session", name="bootstrap_initialized")
def bootstrap_initialized_fixture():
    """Initialize terraform for bootstrap state access."""
    return terraform_init(BOOTSTRAP_DIR)


@pytest.fixture(scope="session", name="bootstrap_outputs")
def bootstrap_outputs_fixture(bootstrap_initialized):
    """Get bootstrap terraform outputs."""
    if not bootstrap_initialized:
        pytest.skip("Terraform init failed for bootstrap")
    return {
        "arn_for_central_logs_bucket": terraform_output(
            BOOTSTRAP_DIR, "arn_for_central_logs_bucket"
        ),
        "arn_for_github_actions_role": terraform_output(
            BOOTSTRAP_DIR, "arn_for_github_actions_role"
        ),
        "arn_for_state_bucket": terraform_output(
            BOOTSTRAP_DIR, "arn_for_state_bucket"
        ),
    }


@pytest.fixture(scope="session", name="central_logs_bucket_name")
def central_logs_bucket_name_fixture(bootstrap_outputs):
    """Extract the central logs bucket name from its ARN."""
    arn = bootstrap_outputs.get("arn_for_central_logs_bucket", "")
    if not arn:
        return ""
    match = re.match(r"arn:aws:s3:::(.+)$", arn)
    return match.group(1) if match else ""
