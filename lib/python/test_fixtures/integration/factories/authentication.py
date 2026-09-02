from typing import Any

from botocore.exceptions import ClientError
import pytest
from test_fixtures.integration.helpers import (
    check_s3_head_bucket_permission,
    NO_CREDENTIALS_MESSAGE,
)


def create_layer1_authentication_tests() -> type:
    class TestAWSAuthentication:
        def test_credentials_available(self, sts_client: Any) -> None:
            assert sts_client is not None, NO_CREDENTIALS_MESSAGE

        def test_can_call_sts_api(self, sts_client: Any) -> None:
            try:
                response = sts_client.get_caller_identity()
                assert response.get("Account"), "STS returned no account ID"
            except ClientError as e:
                pytest.fail(
                    f"Credentials invalid or expired: {e.response['Error']['Message']}"
                )

        def test_identity_has_arn(self, sts_client: Any) -> None:
            response = sts_client.get_caller_identity()
            assert "Arn" in response, "STS response missing Arn field"

    return TestAWSAuthentication


def create_simple_layer1_authentication_tests() -> type:
    class TestAWSAuthentication:
        def test_aws_credentials_valid(self, sts_client: Any) -> None:
            response = sts_client.get_caller_identity()
            assert response["Account"] is not None

        def test_aws_credentials_not_expired(self, sts_client: Any) -> None:
            response = sts_client.get_caller_identity()
            assert "Arn" in response

    return TestAWSAuthentication


def create_layer2_s3_authorization_tests() -> type:
    class TestS3Authorization:
        def test_can_call_s3_head_bucket(self, s3_client: Any, state_bucket_name: str) -> None:
            check_s3_head_bucket_permission(s3_client, state_bucket_name)

        def test_bucket_name_is_configured(self, state_bucket_name: str) -> None:
            assert state_bucket_name, "State bucket name is not configured"

    return TestS3Authorization
