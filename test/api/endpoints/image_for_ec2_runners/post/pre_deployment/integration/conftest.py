"""Pytest fixtures for pre-deployment integration tests.

Common fixtures (terraform_init, terraform_output, terraform_output_json) are
inherited from test/api/conftest.py.
"""
import json

from test.api.conftest import (
    API_BACKEND_DIR,
    terraform_init,
    terraform_output,
    terraform_output_json,
)

import boto3
import pytest


@pytest.fixture(scope="session")
def terraform_initialized():
    """Terraform initialized."""
    return terraform_init(API_BACKEND_DIR)


@pytest.fixture(scope="session")
def ec2_client(aws_region):
    """Ec2 client."""
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(scope="session")
def iam_client(aws_region):
    """Iam client."""
    return boto3.client("iam", region_name=aws_region)


@pytest.fixture(scope="session")
def terraform_outputs(request):
    """Terraform outputs."""
    initialized = request.getfixturevalue("terraform_initialized")
    result = {}
    if initialized:
        result = {
            "ec2_runner_ami_purpose_value": terraform_output(
                API_BACKEND_DIR, "ec2_runner_ami_purpose_value"
            ),
            "ec2_runner_ami_stable_tag": terraform_output(
                API_BACKEND_DIR, "ec2_runner_ami_stable_tag"
            ),
            "runner_security_group_id": terraform_output(
                API_BACKEND_DIR, "runner_security_group_id"
            ),
            "ssm_parameter_name_for_latest_ami": terraform_output(
                API_BACKEND_DIR, "ssm_parameter_name_for_latest_ami"
            ),
            "vpc_public_subnet_ids": terraform_output(
                API_BACKEND_DIR, "vpc_public_subnet_ids"
            ),
            "ec2_instance_types": terraform_output_json(
                API_BACKEND_DIR, "ec2_instance_types"
            ),
        }
    return result


@pytest.fixture(scope="session")
def security_group_id(request):
    """Security group id."""
    outputs = request.getfixturevalue("terraform_outputs")
    return outputs.get("runner_security_group_id", "")


@pytest.fixture(scope="session")
def subnet_ids(request):
    """Subnet ids."""
    outputs = request.getfixturevalue("terraform_outputs")
    raw = outputs.get("vpc_public_subnet_ids", "")
    result = [s.strip() for s in raw.split(",") if s.strip()]
    return result


@pytest.fixture(scope="session")
def instance_types(request):
    """Instance types."""
    outputs = request.getfixturevalue("terraform_outputs")
    raw = outputs.get("ec2_instance_types", "[]")
    result = []
    if raw:
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = []
    return result


@pytest.fixture(scope="session")
def ssm_client(aws_region):
    """Create an SSM client for the test session."""
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(scope="session")
def source_ami_pattern(config):
    """Source ami pattern."""

    result = {
        "os_family": config.get("os_family", ""),
        "os_version": config.get("os_version", ""),
        "os_architecture": config.get("os_architecture", "arm64"),
    }
    return result


@pytest.fixture(scope="session")
def source_ami_id(request):
    """Fetch the AMI ID for the source_ami specified in config.json.

    Uses the exact AMI name (e.g., debian-13-arm64-20251117-2299) from
    config.json to look up the corresponding AMI ID.
    """
    client = request.getfixturevalue("ec2_client")
    cfg = request.getfixturevalue("config")
    source_ami_name = cfg.get("source_ami", "")

    if not source_ami_name:
        pytest.skip("source_ami not configured in config.json")

    response = client.describe_images(
        Filters=[
            {"Name": "name", "Values": [source_ami_name]},
            {"Name": "state", "Values": ["available"]},
        ],
        Owners=["amazon", "aws-marketplace"],
    )

    images = response.get("Images", [])
    if not images:
        pytest.skip(f"AMI not found: {source_ami_name}")

    return images[0]["ImageId"]
