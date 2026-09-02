from typing import Any

import boto3
import pytest


@pytest.fixture(scope="session")
def dynamodb_client(request: pytest.FixtureRequest) -> Any:
    region = request.getfixturevalue("aws_region")
    return boto3.client("dynamodb", region_name=region)
