import os
from typing import Any, Dict

import boto3
import pytest

from .helpers import get_aws_region, get_github_repo


@pytest.fixture(scope="module")
def aws_region() -> str:
    return get_aws_region()


@pytest.fixture(scope="module")
def github_repo() -> str:
    return get_github_repo()


@pytest.fixture(scope="module")
def config() -> Dict[str, Any]:
    return {
        'aws_region': get_aws_region(),
        'github_repo': get_github_repo(),
    }


@pytest.fixture(scope="session")
def ec2_client(aws_region):
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(scope="session")
def ssm_client(aws_region):
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(scope="session")
def test_ami_id():
    return os.environ.get("TEST_AMI_ID", "")
