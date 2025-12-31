"""Authentication and authorization test factory functions."""
from botocore.exceptions import ClientError
import pytest
from test_fixtures.integration.helpers import (
    check_s3_head_bucket_permission,
    NO_CREDENTIALS_MESSAGE,
)


def create_layer1_authentication_tests():
    """Create Layer 1 authentication test class.

    Returns a test class with standard AWS credential verification tests.
    Used by ecs_runner, image_for_ecs_runners, and similar endpoints.

    Returns:
        Test class with Layer 1 authentication tests
    """

    class TestAWSAuthentication:
        """Layer 1: Authentication tests - Verify AWS credentials."""

        def test_credentials_available(self, sts_client):
            """Verify AWS credentials are configured."""
            assert sts_client is not None, NO_CREDENTIALS_MESSAGE

        def test_can_call_sts_api(self, sts_client):
            """Verify credentials are valid by calling STS."""
            try:
                response = sts_client.get_caller_identity()
                assert response.get("Account"), "STS returned no account ID"
            except ClientError as e:
                pytest.fail(
                    f"Credentials invalid or expired: {e.response['Error']['Message']}"
                )

        def test_identity_has_arn(self, sts_client):
            """Verify identity response has Arn."""
            response = sts_client.get_caller_identity()
            assert "Arn" in response, "STS response missing Arn field"

    return TestAWSAuthentication


def create_simple_layer1_authentication_tests():
    """Create simple Layer 1 authentication tests.

    Simpler version with just two basic credential checks.
    Used by bootstrap, www_common, and similar modules.

    Returns:
        Test class with simple authentication tests
    """

    class TestAWSAuthentication:
        """Layer 1: Authentication tests - Verify AWS credentials."""

        def test_aws_credentials_valid(self, sts_client):
            """Verify AWS credentials are valid."""
            response = sts_client.get_caller_identity()
            assert response["Account"] is not None

        def test_aws_credentials_not_expired(self, sts_client):
            """Verify AWS credentials are not expired."""
            response = sts_client.get_caller_identity()
            assert "Arn" in response

    return TestAWSAuthentication


def create_layer2_s3_authorization_tests():
    """Create Layer 2 S3 authorization tests.

    Tests permission to call s3:HeadBucket on the state bucket.
    Requires `s3_client` and `state_bucket_name` fixtures.

    Returns:
        Test class with S3 authorization tests
    """

    class TestS3Authorization:
        """Layer 2: Verify S3 authorization."""

        def test_can_call_s3_head_bucket(self, s3_client, state_bucket_name):
            """Verify permission to call s3:HeadBucket on state bucket."""
            check_s3_head_bucket_permission(s3_client, state_bucket_name)

        def test_bucket_name_is_configured(self, state_bucket_name):
            """Verify state bucket name is configured."""
            assert state_bucket_name, "State bucket name is not configured"

    return TestS3Authorization
