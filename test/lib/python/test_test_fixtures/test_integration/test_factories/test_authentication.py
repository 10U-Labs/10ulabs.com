from unittest.mock import MagicMock

import pytest

from boto_mocks import create_client_error
from test_fixtures.integration.base_classes import (
    Layer2APIGatewayAuthorizationTests,
    Layer2LambdaAndIAMAuthorizationTests,
)
from test_fixtures.integration.factories.authentication import (
    create_api_gateway_authorization_tests,
    create_lambda_and_iam_authorization_tests,
    create_layer1_authentication_tests,
    create_layer2_s3_authorization_tests,
    create_simple_layer1_authentication_tests,
)
from test_fixtures.outcomes import accepted


def test_create_layer1_authentication_tests_returns_class() -> None:
    test_class = create_layer1_authentication_tests()
    assert isinstance(test_class, type)


def test_create_layer1_authentication_tests_returns_class_with_name() -> None:
    test_class = create_layer1_authentication_tests()
    assert test_class.__name__ == "TestAWSAuthentication"


def test_has_test_credentials_available_method() -> None:
    test_class = create_layer1_authentication_tests()
    assert hasattr(test_class, "test_credentials_available")


def test_has_test_can_call_sts_api_method() -> None:
    test_class = create_layer1_authentication_tests()
    assert hasattr(test_class, "test_can_call_sts_api")


def test_has_test_identity_has_arn_method() -> None:
    test_class = create_layer1_authentication_tests()
    assert hasattr(test_class, "test_identity_has_arn")


def test_create_layer1_authentication_tests_credentials_available() -> None:
    test_class = create_layer1_authentication_tests()
    instance = test_class()
    mock_client = MagicMock()
    assert accepted(instance.test_credentials_available, mock_client)


def test_create_layer1_authentication_tests_does_not_raise_with_valid_response() -> None:
    test_class = create_layer1_authentication_tests()
    instance = test_class()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
    instance.test_can_call_sts_api(mock_client)
    assert mock_client.get_caller_identity.called


def test_fails_when_response_has_no_account() -> None:
    test_class = create_layer1_authentication_tests()
    instance = test_class()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {}
    with pytest.raises(AssertionError):
        instance.test_can_call_sts_api(mock_client)


def test_fails_when_client_raises_error() -> None:
    test_class = create_layer1_authentication_tests()
    instance = test_class()
    mock_client = MagicMock()
    mock_client.get_caller_identity.side_effect = create_client_error(
        "ExpiredToken"
    )
    with pytest.raises(pytest.fail.Exception):
        instance.test_can_call_sts_api(mock_client)


def test_create_layer1_authentication_tests_does_not_raise_when_arn_present() -> None:
    test_class = create_layer1_authentication_tests()
    instance = test_class()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {"Arn": "arn:aws:iam::123:role/Test"}
    instance.test_identity_has_arn(mock_client)
    assert mock_client.get_caller_identity.called


def test_create_layer1_authentication_tests_fails_when_arn_missing() -> None:
    test_class = create_layer1_authentication_tests()
    instance = test_class()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {"Account": "123"}
    with pytest.raises(AssertionError):
        instance.test_identity_has_arn(mock_client)


def test_create_simple_layer1_authentication_tests_returns_class() -> None:
    test_class = create_simple_layer1_authentication_tests()
    assert isinstance(test_class, type)


def test_create_simple_layer1_authentication_tests_returns_class_with_name() -> None:
    test_class = create_simple_layer1_authentication_tests()
    assert test_class.__name__ == "TestAWSAuthentication"


def test_has_test_aws_credentials_valid_method() -> None:
    test_class = create_simple_layer1_authentication_tests()
    assert hasattr(test_class, "test_aws_credentials_valid")


def test_has_test_aws_credentials_not_expired_method() -> None:
    test_class = create_simple_layer1_authentication_tests()
    assert hasattr(test_class, "test_aws_credentials_not_expired")


def test_create_simple_layer1_authentication_tests_does_not_raise_with_valid_response() -> None:
    test_class = create_simple_layer1_authentication_tests()
    instance = test_class()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
    instance.test_aws_credentials_valid(mock_client)
    assert mock_client.get_caller_identity.called


def test_fails_when_account_is_none() -> None:
    test_class = create_simple_layer1_authentication_tests()
    instance = test_class()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {"Account": None}
    with pytest.raises(AssertionError):
        instance.test_aws_credentials_valid(mock_client)


def test_create_simple_layer1_authentication_tests_does_not_raise_when_arn_present() -> None:
    test_class = create_simple_layer1_authentication_tests()
    instance = test_class()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {"Arn": "arn:aws:iam::123:role/Test"}
    instance.test_aws_credentials_not_expired(mock_client)
    assert mock_client.get_caller_identity.called


def test_create_simple_layer1_authentication_tests_fails_when_arn_missing() -> None:
    test_class = create_simple_layer1_authentication_tests()
    instance = test_class()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {"Account": "123"}
    with pytest.raises(AssertionError):
        instance.test_aws_credentials_not_expired(mock_client)


def test_create_layer2_s3_authorization_tests_returns_class() -> None:
    test_class = create_layer2_s3_authorization_tests()
    assert isinstance(test_class, type)


def test_create_layer2_s3_authorization_tests_returns_class_with_name() -> None:
    test_class = create_layer2_s3_authorization_tests()
    assert test_class.__name__ == "TestS3Authorization"


def test_has_test_can_call_s3_head_bucket_method() -> None:
    test_class = create_layer2_s3_authorization_tests()
    assert hasattr(test_class, "test_can_call_s3_head_bucket")


def test_has_test_bucket_name_is_configured_method() -> None:
    test_class = create_layer2_s3_authorization_tests()
    assert hasattr(test_class, "test_bucket_name_is_configured")


def test_create_layer2_s3_authorization_tests_can_call_head_bucket() -> None:
    test_class = create_layer2_s3_authorization_tests()
    instance = test_class()
    mock_client = MagicMock()
    mock_client.head_bucket.return_value = {}
    instance.test_can_call_s3_head_bucket(mock_client, "my-bucket")
    assert mock_client.head_bucket.called


def test_does_not_raise_when_bucket_name_provided() -> None:
    test_class = create_layer2_s3_authorization_tests()
    instance = test_class()
    assert accepted(instance.test_bucket_name_is_configured, "my-bucket")


def test_fails_when_bucket_name_empty() -> None:
    test_class = create_layer2_s3_authorization_tests()
    instance = test_class()
    with pytest.raises(AssertionError):
        instance.test_bucket_name_is_configured("")


def test_fails_when_bucket_name_none() -> None:
    test_class = create_layer2_s3_authorization_tests()
    instance = test_class()
    with pytest.raises(AssertionError):
        instance.test_bucket_name_is_configured(None)


def test_create_api_gateway_authorization_tests_returns_class() -> None:
    test_class = create_api_gateway_authorization_tests()
    assert isinstance(test_class, type)


def test_create_api_gateway_authorization_tests_returns_layer2_base_class() -> None:
    test_class = create_api_gateway_authorization_tests()
    assert test_class is Layer2APIGatewayAuthorizationTests


def test_has_test_can_describe_rest_apis_method() -> None:
    test_class = create_api_gateway_authorization_tests()
    assert hasattr(test_class, "test_can_describe_rest_apis")


def test_has_test_can_access_specific_rest_api_method() -> None:
    test_class = create_api_gateway_authorization_tests()
    assert hasattr(test_class, "test_can_access_specific_rest_api")


def test_create_lambda_and_iam_authorization_tests_returns_class() -> None:
    test_class = create_lambda_and_iam_authorization_tests()
    assert isinstance(test_class, type)


def test_create_lambda_and_iam_authorization_tests_returns_layer2_base_class() -> None:
    test_class = create_lambda_and_iam_authorization_tests()
    assert test_class is Layer2LambdaAndIAMAuthorizationTests


def test_has_test_can_list_functions_method() -> None:
    test_class = create_lambda_and_iam_authorization_tests()
    assert hasattr(test_class, "test_can_list_functions")


def test_has_test_can_list_roles_method() -> None:
    test_class = create_lambda_and_iam_authorization_tests()
    assert hasattr(test_class, "test_can_list_roles")
