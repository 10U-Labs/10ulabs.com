"""Unit tests for test_fixtures.integration.factories.authentication module."""
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from test_fixtures.integration.factories.authentication import (
    create_layer1_authentication_tests,
    create_layer2_s3_authorization_tests,
    create_simple_layer1_authentication_tests,
)


def _create_client_error(code: str, message: str = "Test error") -> ClientError:
    """Create a ClientError for testing."""
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "TestOperation"
    )


# === create_layer1_authentication_tests ===


class TestCreateLayer1AuthenticationTestsReturnsClass:
    """Tests for create_layer1_authentication_tests return type."""

    def test_returns_class(self):
        """create_layer1_authentication_tests returns a class."""
        test_class = create_layer1_authentication_tests()
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_layer1_authentication_tests returns class named TestAWSAuthentication."""
        test_class = create_layer1_authentication_tests()
        assert test_class.__name__ == "TestAWSAuthentication"


class TestCreateLayer1AuthenticationTestsHasMethods:
    """Tests for create_layer1_authentication_tests class methods."""

    def test_has_test_credentials_available_method(self):
        """create_layer1_authentication_tests class has test_credentials_available."""
        test_class = create_layer1_authentication_tests()
        assert hasattr(test_class, "test_credentials_available")

    def test_has_test_can_call_sts_api_method(self):
        """create_layer1_authentication_tests class has test_can_call_sts_api."""
        test_class = create_layer1_authentication_tests()
        assert hasattr(test_class, "test_can_call_sts_api")

    def test_has_test_identity_has_arn_method(self):
        """create_layer1_authentication_tests class has test_identity_has_arn."""
        test_class = create_layer1_authentication_tests()
        assert hasattr(test_class, "test_identity_has_arn")


class TestCreateLayer1AuthenticationTestsCredentialsAvailable:
    """Tests for test_credentials_available method."""

    def test_does_not_raise_with_valid_client(self):
        """test_credentials_available does not raise with valid client."""
        test_class = create_layer1_authentication_tests()
        instance = test_class()
        mock_client = MagicMock()
        instance.test_credentials_available(mock_client)


class TestCreateLayer1AuthenticationTestsCanCallStsApi:
    """Tests for test_can_call_sts_api method."""

    def test_does_not_raise_with_valid_response(self):
        """test_can_call_sts_api does not raise with valid response."""
        test_class = create_layer1_authentication_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
        instance.test_can_call_sts_api(mock_client)

    def test_fails_when_response_has_no_account(self):
        """test_can_call_sts_api fails when response has no Account."""
        test_class = create_layer1_authentication_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {}
        with pytest.raises(AssertionError):
            instance.test_can_call_sts_api(mock_client)

    def test_fails_when_client_raises_error(self):
        """test_can_call_sts_api fails when client raises ClientError."""
        test_class = create_layer1_authentication_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_caller_identity.side_effect = _create_client_error(
            "ExpiredToken"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_call_sts_api(mock_client)


class TestCreateLayer1AuthenticationTestsIdentityHasArn:
    """Tests for test_identity_has_arn method."""

    def test_does_not_raise_when_arn_present(self):
        """test_identity_has_arn does not raise when Arn present."""
        test_class = create_layer1_authentication_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Arn": "arn:aws:iam::123:role/Test"}
        instance.test_identity_has_arn(mock_client)

    def test_fails_when_arn_missing(self):
        """test_identity_has_arn fails when Arn missing."""
        test_class = create_layer1_authentication_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123"}
        with pytest.raises(AssertionError):
            instance.test_identity_has_arn(mock_client)


# === create_simple_layer1_authentication_tests ===


class TestCreateSimpleLayer1AuthenticationTestsReturnsClass:
    """Tests for create_simple_layer1_authentication_tests return type."""

    def test_returns_class(self):
        """create_simple_layer1_authentication_tests returns a class."""
        test_class = create_simple_layer1_authentication_tests()
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_simple_layer1_authentication_tests returns class named TestAWSAuthentication."""
        test_class = create_simple_layer1_authentication_tests()
        assert test_class.__name__ == "TestAWSAuthentication"


class TestCreateSimpleLayer1AuthenticationTestsHasMethods:
    """Tests for create_simple_layer1_authentication_tests class methods."""

    def test_has_test_aws_credentials_valid_method(self):
        """create_simple_layer1_authentication_tests has test_aws_credentials_valid."""
        test_class = create_simple_layer1_authentication_tests()
        assert hasattr(test_class, "test_aws_credentials_valid")

    def test_has_test_aws_credentials_not_expired_method(self):
        """create_simple_layer1_authentication_tests has test_aws_credentials_not_expired."""
        test_class = create_simple_layer1_authentication_tests()
        assert hasattr(test_class, "test_aws_credentials_not_expired")


class TestCreateSimpleLayer1AuthenticationTestsCredentialsValid:
    """Tests for test_aws_credentials_valid method."""

    def test_does_not_raise_with_valid_response(self):
        """test_aws_credentials_valid does not raise with valid response."""
        test_class = create_simple_layer1_authentication_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
        instance.test_aws_credentials_valid(mock_client)

    def test_fails_when_account_is_none(self):
        """test_aws_credentials_valid fails when Account is None."""
        test_class = create_simple_layer1_authentication_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": None}
        with pytest.raises(AssertionError):
            instance.test_aws_credentials_valid(mock_client)


class TestCreateSimpleLayer1AuthenticationTestsCredentialsNotExpired:
    """Tests for test_aws_credentials_not_expired method."""

    def test_does_not_raise_when_arn_present(self):
        """test_aws_credentials_not_expired does not raise when Arn present."""
        test_class = create_simple_layer1_authentication_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Arn": "arn:aws:iam::123:role/Test"}
        instance.test_aws_credentials_not_expired(mock_client)

    def test_fails_when_arn_missing(self):
        """test_aws_credentials_not_expired fails when Arn missing."""
        test_class = create_simple_layer1_authentication_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123"}
        with pytest.raises(AssertionError):
            instance.test_aws_credentials_not_expired(mock_client)


# === create_layer2_s3_authorization_tests ===


class TestCreateLayer2S3AuthorizationTestsReturnsClass:
    """Tests for create_layer2_s3_authorization_tests return type."""

    def test_returns_class(self):
        """create_layer2_s3_authorization_tests returns a class."""
        test_class = create_layer2_s3_authorization_tests()
        assert isinstance(test_class, type)

    def test_returns_class_with_name(self):
        """create_layer2_s3_authorization_tests returns class named TestS3Authorization."""
        test_class = create_layer2_s3_authorization_tests()
        assert test_class.__name__ == "TestS3Authorization"


class TestCreateLayer2S3AuthorizationTestsHasMethods:
    """Tests for create_layer2_s3_authorization_tests class methods."""

    def test_has_test_can_call_s3_head_bucket_method(self):
        """create_layer2_s3_authorization_tests has test_can_call_s3_head_bucket."""
        test_class = create_layer2_s3_authorization_tests()
        assert hasattr(test_class, "test_can_call_s3_head_bucket")

    def test_has_test_bucket_name_is_configured_method(self):
        """create_layer2_s3_authorization_tests has test_bucket_name_is_configured."""
        test_class = create_layer2_s3_authorization_tests()
        assert hasattr(test_class, "test_bucket_name_is_configured")


class TestCreateLayer2S3AuthorizationTestsCanCallHeadBucket:
    """Tests for test_can_call_s3_head_bucket method."""

    def test_does_not_raise_with_accessible_bucket(self):
        """test_can_call_s3_head_bucket does not raise with accessible bucket."""
        test_class = create_layer2_s3_authorization_tests()
        instance = test_class()
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = {}
        instance.test_can_call_s3_head_bucket(mock_client, "my-bucket")


class TestCreateLayer2S3AuthorizationTestsBucketNameConfigured:
    """Tests for test_bucket_name_is_configured method."""

    def test_does_not_raise_when_bucket_name_provided(self):
        """test_bucket_name_is_configured does not raise with bucket name."""
        test_class = create_layer2_s3_authorization_tests()
        instance = test_class()
        instance.test_bucket_name_is_configured("my-bucket")

    def test_fails_when_bucket_name_empty(self):
        """test_bucket_name_is_configured fails when bucket name empty."""
        test_class = create_layer2_s3_authorization_tests()
        instance = test_class()
        with pytest.raises(AssertionError):
            instance.test_bucket_name_is_configured("")

    def test_fails_when_bucket_name_none(self):
        """test_bucket_name_is_configured fails when bucket name None."""
        test_class = create_layer2_s3_authorization_tests()
        instance = test_class()
        with pytest.raises(AssertionError):
            instance.test_bucket_name_is_configured(None)
