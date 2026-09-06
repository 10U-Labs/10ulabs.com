from typing import Any

import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import (
    create_api_gateway_authorization_tests,
    create_lambda_and_iam_authorization_tests,
)


TestAPIGatewayAuthorization = create_api_gateway_authorization_tests()
TestLambdaAndIAMAuthorization = create_lambda_and_iam_authorization_tests()


def test_can_get_account_sending_enabled(ses_client: Any) -> None:
    try:
        ses_client.get_account_sending_enabled()
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail("No permission to check SES account sending status")
        raise
    assert True


def test_can_list_identities(ses_client: Any) -> None:
    try:
        ses_client.list_identities(MaxItems=1)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail("No permission to list SES identities")
        raise
    assert True


def test_can_describe_parameters(ssm_client: Any) -> None:
    try:
        ssm_client.describe_parameters(MaxResults=1)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            pytest.fail("No permission to describe SSM parameters")
        raise
    assert True
