"""Pytest fixtures for pre-deployment integration tests."""
import json
import subprocess
from pathlib import Path

import boto3
import pytest


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent.parent
BACKEND_DIR = REPO_ROOT / "src" / "api" / "backend"


def _run_terraform_output(output_name: str, as_json: bool = False) -> str:
    """ run terraform output."""

    cmd = ["terraform", "output"]
    if as_json:
        cmd.append("-json")
    else:
        cmd.append("-raw")
    cmd.append(output_name)
    result = subprocess.run(
        cmd,
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
        check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _terraform_init() -> bool:
    """ terraform init."""

    result = subprocess.run(
        ["terraform", "init", "-backend=true", "-input=false"],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
        check=False
    )
    return result.returncode == 0


@pytest.fixture(scope="session")
def terraform_initialized():
    """Terraform initialized."""

    success = _terraform_init()
    return success


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
            "ec2_runner_ami_purpose_value": _run_terraform_output("ec2_runner_ami_purpose_value"),
            "ec2_runner_ami_stable_tag": _run_terraform_output("ec2_runner_ami_stable_tag"),
            "runner_security_group_id": _run_terraform_output("runner_security_group_id"),
            "ssm_parameter_name_for_latest_ami": _run_terraform_output(
                "ssm_parameter_name_for_latest_ami"
            ),
            "vpc_public_subnet_ids": _run_terraform_output("vpc_public_subnet_ids"),
            "ec2_instance_types": _run_terraform_output("ec2_instance_types", as_json=True),
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
    """Fetch the AMI ID for the source_ami specified in config.yml.

    Uses the exact AMI name (e.g., debian-13-arm64-20251117-2299) from
    config.yml to look up the corresponding AMI ID.
    """
    client = request.getfixturevalue("ec2_client")
    cfg = request.getfixturevalue("config")
    source_ami_name = cfg.get("source_ami", "")

    if not source_ami_name:
        pytest.skip("source_ami not configured in config.yml")

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
