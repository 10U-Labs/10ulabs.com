"""Pytest fixtures for pre-deployment integration tests.

Common fixtures (terraform_init, terraform_output) are inherited from
test/api/conftest.py.
"""
from test.api.conftest import (
    REPO_ROOT,
    get_runners_outputs,
    terraform_init,
    terraform_output,
)

import boto3
import pytest

pytest_plugins = ['pytest_layers']

IMAGE_FOR_EC2_RUNNERS_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ec2_runners"
RUNNERS_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "webhooks" / "github" / "jit_runner_requests"


@pytest.fixture(scope="session")
def ec2_client(aws_region):
    """Create an EC2 client."""
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(scope="session")
def image_for_ec2_runners_terraform_initialized():
    """Initialize terraform for image_for_ec2_runners state access."""
    return terraform_init(IMAGE_FOR_EC2_RUNNERS_DIR)


@pytest.fixture(scope="session")
def runners_terraform_initialized():
    """Initialize terraform for runners state access."""
    return terraform_init(RUNNERS_DIR)


@pytest.fixture(scope="session")
def image_for_ec2_runners_outputs(request):
    """Get image_for_ec2_runners terraform outputs."""
    if not request.getfixturevalue("image_for_ec2_runners_terraform_initialized"):
        pytest.skip("Terraform init failed for image_for_ec2_runners")
    return {
        "lambda_function_arn": terraform_output(
            IMAGE_FOR_EC2_RUNNERS_DIR, "lambda_function_arn"
        ),
        "lambda_function_name": terraform_output(
            IMAGE_FOR_EC2_RUNNERS_DIR, "lambda_function_name"
        ),
        "lambda_invoke_arn": terraform_output(
            IMAGE_FOR_EC2_RUNNERS_DIR, "lambda_invoke_arn"
        ),
    }


@pytest.fixture(scope="session")
def runners_outputs(request):
    """Get runners terraform outputs for EC2 runner tests."""
    if not request.getfixturevalue("runners_terraform_initialized"):
        pytest.skip("Terraform init failed for runners")
    return get_runners_outputs(RUNNERS_DIR)


def get_stable_ami_filters():
    """Return the filters for finding stable EC2 runner AMIs."""
    return [
        {"Name": "tag:Purpose", "Values": ["GitHub self-hosted EC2 runner"]},
        {"Name": "tag:Stable", "Values": ["true"]},
    ]


def get_stable_ami_info(client):
    """Get the stable AMI ID and architecture, or None if not found."""
    response = client.describe_images(
        Owners=["self"],
        Filters=get_stable_ami_filters()
    )
    if not response["Images"]:
        return None
    image = response["Images"][0]
    return {"id": image["ImageId"], "arch": image.get("Architecture", "x86_64")}
