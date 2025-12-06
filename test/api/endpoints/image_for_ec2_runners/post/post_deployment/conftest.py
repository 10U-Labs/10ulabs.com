"""Pytest fixtures for post-deployment tests."""
# pylint: disable=missing-function-docstring
import os
import sys
import time
from pathlib import Path
import boto3
import pytest

sys.path.insert(0, str(Path(__file__).parent))


def execute_ssm_command(client, instance_id, command, wait_seconds=5):
    response = client.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [command]}
    )
    command_id = response["Command"]["CommandId"]
    time.sleep(wait_seconds)
    output = client.get_command_invocation(
        CommandId=command_id,
        InstanceId=instance_id
    )
    return output


@pytest.fixture
def run_ssm_command():
    return execute_ssm_command


@pytest.fixture(scope="session")
def ec2_client(aws_region):
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(scope="session")
def ssm_client(aws_region):
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(scope="session")
def logs_client(aws_region):
    return boto3.client("logs", region_name=aws_region)


@pytest.fixture(scope="session")
def test_ami_id():
    return os.environ.get("TEST_AMI_ID", "")


@pytest.fixture(scope="session")
def github_token():
    return os.environ.get("GITHUB_PAT", "")


@pytest.fixture(scope="session")
def github_repo():
    return os.environ.get("GITHUB_REPOSITORY", "10U-Labs-LLC/10ulabs.com")
