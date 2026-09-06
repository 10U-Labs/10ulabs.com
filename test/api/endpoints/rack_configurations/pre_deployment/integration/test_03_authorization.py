from typing import Any

import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import (
    create_api_gateway_authorization_tests,
    create_lambda_and_iam_authorization_tests,
)


TestAPIGatewayAuthorization = create_api_gateway_authorization_tests()
TestLambdaAndIAMAuthorization = create_lambda_and_iam_authorization_tests()


def test_can_list_tables(dynamodb_client: Any) -> None:
    try:
        dynamodb_client.list_tables(Limit=1)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            pytest.fail("No permission to list DynamoDB tables")
        raise
    assert True


def test_can_list_buckets(s3_client: Any) -> None:
    try:
        s3_client.list_buckets()
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail("No permission to list S3 buckets")
        raise
    assert True
