from typing import Any

import test_fixtures.integration as integration_module


def _get_class(name: str) -> Any:
    return getattr(integration_module, name)


Layer2EndpointAuthenticationTests = _get_class("Layer2EndpointAuthenticationTests")


def test_layer2_endpoint_authentication_tests_class_exists() -> None:
    assert Layer2EndpointAuthenticationTests is not None


def test_has_aws_credentials_are_valid_test() -> None:
    assert hasattr(
        Layer2EndpointAuthenticationTests, "test_aws_credentials_are_valid"
    )


def test_has_aws_credentials_return_account_id_test() -> None:
    assert hasattr(
        Layer2EndpointAuthenticationTests, "test_aws_credentials_return_account_id"
    )


def test_has_aws_credentials_return_arn_test() -> None:
    assert hasattr(
        Layer2EndpointAuthenticationTests, "test_aws_credentials_return_arn"
    )


def test_has_aws_credentials_arn_has_valid_format_test() -> None:
    assert hasattr(
        Layer2EndpointAuthenticationTests, "test_aws_credentials_arn_has_valid_format"
    )
