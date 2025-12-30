"""Pytest fixtures for pre-deployment integration tests.

Common fixtures (terraform_init, terraform_output) are inherited from
test/api/conftest.py. terraform_output_json is imported directly from
test_fixtures.terraform.
"""
import json

from test.api.conftest import (
    API_BACKEND_DIR,
    terraform_init,
    terraform_output,
)
from test_fixtures.terraform import terraform_output_json

import boto3
import pytest
from botocore.exceptions import ClientError


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
            "security_group_id_for_runners": terraform_output(
                API_BACKEND_DIR, "security_group_id_for_runners"
            ),
            "ssm_parameter_name_for_latest_ami": terraform_output(
                API_BACKEND_DIR, "ssm_parameter_name_for_latest_ami"
            ),
            "public_subnet_ids": terraform_output(
                API_BACKEND_DIR, "public_subnet_ids"
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
    return outputs.get("security_group_id_for_runners", "")


@pytest.fixture(scope="session")
def subnet_ids(request):
    """Subnet ids."""
    outputs = request.getfixturevalue("terraform_outputs")
    raw = outputs.get("public_subnet_ids", "")
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
def sts_client(aws_region):
    """Create an STS client for authentication tests."""
    return boto3.client("sts", region_name=aws_region)


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
def instance_profile_name(config):
    """Get instance profile name from config."""
    return config.get("github_runner_iam_instance_profile_name", "")


@pytest.fixture(scope="session")
def fetched_instance_profile(request):
    """Fetch instance profile from IAM.

    Returns the instance profile dict or None if not found.
    """
    client = request.getfixturevalue("iam_client")
    profile_name = request.getfixturevalue("instance_profile_name")

    if not profile_name:
        return None

    try:
        response = client.get_instance_profile(InstanceProfileName=profile_name)
        return response.get("InstanceProfile", {})
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            return None
        raise


@pytest.fixture(scope="session")
def source_ami_pattern_configured(request):
    """Check if source AMI pattern is configured.

    Returns True if os_family and os_version are set.
    """
    pattern = request.getfixturevalue("source_ami_pattern")
    return bool(pattern.get("os_family") and pattern.get("os_version"))


@pytest.fixture(scope="session")
def source_ami_images(request):
    """Fetch matching AMIs for the source_ami_pattern.

    Returns a list of AMI images matching the OS family, version, and
    architecture from the source_ami_pattern fixture.
    """
    client = request.getfixturevalue("ec2_client")
    pattern = request.getfixturevalue("source_ami_pattern")

    os_family = pattern.get("os_family", "")
    os_version = pattern.get("os_version", "")
    os_arch = pattern.get("os_architecture", "arm64")

    if not os_family or not os_version:
        return []

    arch_filter = "arm64" if os_arch == "arm64" else "x86_64"
    response = client.describe_images(
        Filters=[
            {"Name": "name", "Values": [f"{os_family}-{os_version}-*"]},
            {"Name": "architecture", "Values": [arch_filter]},
            {"Name": "state", "Values": ["available"]},
        ],
        Owners=["amazon", "self", "aws-marketplace"],
    )

    return response.get("Images", [])


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
