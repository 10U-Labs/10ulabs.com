from test.api.conftest import skip_if_endpoint_not_deployed

import boto3
import pytest

__all__ = ['skip_if_endpoint_not_deployed']


@pytest.fixture(scope="session")
def iam_client(aws_region):
    return boto3.client("iam", region_name=aws_region)
