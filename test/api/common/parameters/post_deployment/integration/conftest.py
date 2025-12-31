"""Post-deployment integration test fixtures for api/common/parameters.

These tests follow the 3-layer testing model from POST_DEPLOYMENT_INTEGRATION_TESTS.md.
"""
from repo_utils import REPO_ROOT
from test_fixtures.terraform import terraform_init, terraform_output

import boto3
import pytest

PARAMETERS_SRC = REPO_ROOT / "src" / "api" / "shared" / "parameters"


@pytest.fixture(scope="session")
def parameters_terraform_initialized():
    """Initialize terraform for parameters state access."""
    return terraform_init(PARAMETERS_SRC)


@pytest.fixture(scope="session")
def parameters_outputs(request):
    """Get parameters terraform outputs."""
    if not request.getfixturevalue("parameters_terraform_initialized"):
        pytest.skip("Terraform init failed for parameters")
    return {
        "ssm_ec2_runner_ami_latest_name": terraform_output(
            PARAMETERS_SRC, "ssm_ec2_runner_ami_latest_name"
        ),
        "ssm_ec2_runner_ami_latest_arn": terraform_output(
            PARAMETERS_SRC, "ssm_ec2_runner_ami_latest_arn"
        ),
    }


@pytest.fixture(scope="session")
def ssm_client(aws_region):
    """Create an SSM client."""
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(scope="session")
def ssm_parameter_name(request):
    """Get the SSM parameter name."""
    outputs = request.getfixturevalue("parameters_outputs")
    return outputs.get("ssm_ec2_runner_ami_latest_name", "")
