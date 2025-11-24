import os
import boto3
import pytest


@pytest.fixture(scope="module")
def ec2_client(aws_region):
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(scope="module")
def ssm_client(aws_region):
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(scope="module")
def logs_client(aws_region):
    return boto3.client("logs", region_name=aws_region)


@pytest.fixture(scope="module")
def test_ami_id():
    return os.environ.get("TEST_AMI_ID", "")


@pytest.fixture(scope="module")
def github_token():
    return os.environ.get("GITHUB_PAT", "")


@pytest.fixture(scope="module")
def github_repo(tfvars):
    return os.environ.get("GITHUB_REPOSITORY", "10U-Labs-LLC/10ulabs.com")
