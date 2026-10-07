from unittest.mock import MagicMock

import pytest

import test_fixtures.integration as integration_module


def test_aws_credentials_are_valid_success() -> None:
    instance = integration_module.Layer2EndpointAuthenticationTests()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
    instance.test_aws_credentials_are_valid(mock_client)
    assert mock_client.get_caller_identity.called


def test_aws_credentials_are_valid_fails_with_none_account() -> None:
    instance = integration_module.Layer2EndpointAuthenticationTests()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {"Account": None}
    with pytest.raises(AssertionError):
        instance.test_aws_credentials_are_valid(mock_client)


def test_aws_credentials_return_account_id_success() -> None:
    instance = integration_module.Layer2EndpointAuthenticationTests()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
    instance.test_aws_credentials_return_account_id(mock_client)
    assert mock_client.get_caller_identity.called


def test_aws_credentials_return_account_id_fails_with_wrong_length() -> None:
    instance = integration_module.Layer2EndpointAuthenticationTests()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {"Account": "12345"}
    with pytest.raises(AssertionError):
        instance.test_aws_credentials_return_account_id(mock_client)


def test_aws_credentials_return_arn_success() -> None:
    instance = integration_module.Layer2EndpointAuthenticationTests()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {
        "Account": "123",
        "Arn": "arn:aws:iam::123:role/MyRole"
    }
    instance.test_aws_credentials_return_arn(mock_client)
    assert mock_client.get_caller_identity.called


def test_aws_credentials_return_arn_fails_without_arn() -> None:
    instance = integration_module.Layer2EndpointAuthenticationTests()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {"Account": "123"}
    with pytest.raises(AssertionError):
        instance.test_aws_credentials_return_arn(mock_client)


def test_aws_credentials_arn_has_valid_format_success() -> None:
    instance = integration_module.Layer2EndpointAuthenticationTests()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {
        "Arn": "arn:aws:iam::123:role/MyRole"
    }
    instance.test_aws_credentials_arn_has_valid_format(mock_client)
    assert mock_client.get_caller_identity.called


def test_aws_credentials_arn_has_valid_format_fails_with_invalid_arn() -> None:
    instance = integration_module.Layer2EndpointAuthenticationTests()
    mock_client = MagicMock()
    mock_client.get_caller_identity.return_value = {"Arn": "invalid-arn"}
    with pytest.raises(AssertionError):
        instance.test_aws_credentials_arn_has_valid_format(mock_client)
