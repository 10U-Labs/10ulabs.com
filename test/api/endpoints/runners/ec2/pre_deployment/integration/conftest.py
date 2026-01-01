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

IMAGE_FOR_EC2_RUNNERS_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ec2" / "images"
NETWORKING_DIR = REPO_ROOT / "src" / "api" / "common" / "networking"


@pytest.fixture(scope="session")
def ec2_client(aws_region):
    """Create an EC2 client."""
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(scope="session")
def ec2_images_terraform_initialized():
    """Initialize terraform for ec2_images state access."""
    return terraform_init(IMAGE_FOR_EC2_RUNNERS_DIR)


@pytest.fixture(scope="session")
def networking_terraform_initialized():
    """Initialize terraform for networking state access."""
    return terraform_init(NETWORKING_DIR)


@pytest.fixture(scope="session")
def ec2_images_outputs(request):
    """Get ec2_images terraform outputs."""
    if not request.getfixturevalue("ec2_images_terraform_initialized"):
        pytest.skip("Terraform init failed for ec2_images")
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
def networking_outputs(request):
    """Get networking terraform outputs for EC2 runner tests."""
    if not request.getfixturevalue("networking_terraform_initialized"):
        pytest.skip("Terraform init failed for networking")
    return get_runners_outputs(NETWORKING_DIR)


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
