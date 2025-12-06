"""Pytest fixtures for pre-deployment integration tests."""
# pylint: disable=missing-function-docstring,line-too-long
import json
import subprocess
from pathlib import Path

import boto3
import pytest


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent.parent
BACKEND_DIR = REPO_ROOT / "src" / "api" / "backend"


def _run_terraform_output(output_name: str, as_json: bool = False) -> str:
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
    success = _terraform_init()
    return success


@pytest.fixture(scope="session")
def ec2_client(aws_region):  # pylint: disable=redefined-outer-name
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(scope="session")
def iam_client(aws_region):  # pylint: disable=redefined-outer-name
    return boto3.client("iam", region_name=aws_region)


@pytest.fixture(scope="session")
def terraform_outputs(terraform_initialized):  # pylint: disable=redefined-outer-name
    result = {}
    if terraform_initialized:
        result = {
            "ec2_runner_ami_purpose_value": _run_terraform_output("ec2_runner_ami_purpose_value"),
            "ec2_runner_ami_stable_tag": _run_terraform_output("ec2_runner_ami_stable_tag"),
            "runner_security_group_id": _run_terraform_output("runner_security_group_id"),
            "ssm_parameter_name_for_latest_ami": _run_terraform_output("ssm_parameter_name_for_latest_ami"),
            "vpc_public_subnet_ids": _run_terraform_output("vpc_public_subnet_ids"),
            "ec2_instance_types": _run_terraform_output("ec2_instance_types", as_json=True),
        }
    return result


@pytest.fixture(scope="session")
def security_group_id(terraform_outputs):  # pylint: disable=redefined-outer-name
    return terraform_outputs.get("runner_security_group_id", "")


@pytest.fixture(scope="session")
def subnet_ids(terraform_outputs):  # pylint: disable=redefined-outer-name
    raw = terraform_outputs.get("vpc_public_subnet_ids", "")
    result = [s.strip() for s in raw.split(",") if s.strip()]
    return result


@pytest.fixture(scope="session")
def instance_types(terraform_outputs):  # pylint: disable=redefined-outer-name
    raw = terraform_outputs.get("ec2_instance_types", "[]")
    result = []
    if raw:
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = []
    return result


@pytest.fixture(scope="session")
def source_ami_pattern(config):  # pylint: disable=redefined-outer-name
    result = {
        "os_family": config.get("os_family", ""),
        "os_version": config.get("os_version", ""),
        "os_architecture": config.get("os_architecture", "arm64"),
    }
    return result
