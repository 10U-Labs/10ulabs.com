from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from boto_mocks import create_client_error
from test_fixtures.integration.factories.infrastructure import (
    create_kms_policy_test,
    create_lambda_role_existence_test,
    create_log_group_configuration_tests,
    create_www_common_fixtures,
    create_www_common_s3_existence_tests,
    handle_ecr_error,
)
from test_fixtures.outcomes import accepted


def _www_common_outputs(
    monkeypatch: pytest.MonkeyPatch,
    terraform_outputs: Any,
    **kwargs: Any
) -> Any:
    monkeypatch.setattr(
        "test_fixtures.integration.factories.infrastructure.terraform_output",
        MagicMock(side_effect=terraform_outputs)
    )
    _, outputs_fixture = create_www_common_fixtures(**kwargs)
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = True
    return outputs_fixture.__wrapped__(mock_request)


def test_returns_tuple() -> None:
    result = create_www_common_fixtures()
    assert isinstance(result, tuple)


def test_returns_two_fixtures() -> None:
    result = create_www_common_fixtures()
    assert len(result) == 2


def test_first_fixture_is_callable() -> None:
    result = create_www_common_fixtures()
    assert callable(result[0])


def test_second_fixture_is_callable() -> None:
    result = create_www_common_fixtures()
    assert callable(result[1])


def test_first_fixture_has_correct_name() -> None:
    result = create_www_common_fixtures()
    assert result[0].__name__ == "www_common_terraform_initialized"


def test_second_fixture_has_correct_name() -> None:
    result = create_www_common_fixtures()
    assert result[1].__name__ == "www_common_outputs"


def test_accepts_include_cloudfront() -> None:
    result = create_www_common_fixtures(include_cloudfront=True)
    assert len(result) == 2


def test_accepts_include_website_domain() -> None:
    result = create_www_common_fixtures(include_website_domain=True)
    assert len(result) == 2


def test_accepts_both_options() -> None:
    result = create_www_common_fixtures(
        include_cloudfront=True, include_website_domain=True
    )
    assert len(result) == 2


def test_terraform_initialized_calls_terraform_init(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_init = MagicMock(return_value=True)
    monkeypatch.setattr(
        "test_fixtures.integration.factories.infrastructure.terraform_init",
        mock_init
    )
    tf_init, _ = create_www_common_fixtures()
    result = tf_init.__wrapped__()
    assert result is True
    mock_init.assert_called_once()


def test_outputs_skips_when_init_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_init = MagicMock(return_value=False)
    mock_output = MagicMock(return_value="value")
    monkeypatch.setattr(
        "test_fixtures.integration.factories.infrastructure.terraform_init",
        mock_init
    )
    monkeypatch.setattr(
        "test_fixtures.integration.factories.infrastructure.terraform_output",
        mock_output
    )
    _, outputs_fixture = create_www_common_fixtures()
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = False
    with pytest.raises(pytest.skip.Exception):
        outputs_fixture.__wrapped__(mock_request)


def test_outputs_returns_bucket_name(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _www_common_outputs(
        monkeypatch, ["my-bucket", "arn:aws:s3:::my-bucket"]
    )
    assert "bucket_name" in result


def test_outputs_returns_bucket_arn(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _www_common_outputs(
        monkeypatch, ["my-bucket", "arn:aws:s3:::my-bucket"]
    )
    assert "bucket_arn" in result


def test_outputs_includes_website_domain_when_requested(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _www_common_outputs(
        monkeypatch,
        ["my-bucket", "arn:aws:s3:::my-bucket", "example.com"],
        include_website_domain=True
    )
    assert "website_domain_name" in result


def test_outputs_includes_cloudfront_when_requested(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _www_common_outputs(
        monkeypatch,
        ["my-bucket", "arn:aws:s3:::my-bucket", "E123456789"],
        include_cloudfront=True
    )
    assert "cloudfront_distribution_id" in result


def test_outputs_includes_website_domain_when_both_requested(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _www_common_outputs(
        monkeypatch,
        ["my-bucket", "arn:aws:s3:::my-bucket", "example.com", "E123456789"],
        include_website_domain=True, include_cloudfront=True
    )
    assert "website_domain_name" in result


def test_outputs_includes_cloudfront_when_both_requested(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _www_common_outputs(
        monkeypatch,
        ["my-bucket", "arn:aws:s3:::my-bucket", "example.com", "E123456789"],
        include_website_domain=True, include_cloudfront=True
    )
    assert "cloudfront_distribution_id" in result


def test_create_www_common_s3_existence_tests_returns_class() -> None:
    test_class = create_www_common_s3_existence_tests()
    assert isinstance(test_class, type)


def test_create_www_common_s3_existence_tests_returns_class_with_name() -> None:
    test_class = create_www_common_s3_existence_tests()
    assert test_class.__name__ == "TestWWWCommonS3Existence"


def test_has_test_bucket_name_output_exists() -> None:
    test_class = create_www_common_s3_existence_tests()
    assert hasattr(test_class, "test_bucket_name_output_exists")


def test_has_test_s3_bucket_exists() -> None:
    test_class = create_www_common_s3_existence_tests()
    assert hasattr(test_class, "test_s3_bucket_exists")


def test_does_not_raise_when_output_exists() -> None:
    test_class = create_www_common_s3_existence_tests()
    instance = test_class()
    outputs = {"bucket_name": "my-bucket"}
    assert accepted(instance.test_bucket_name_output_exists, outputs)


def test_fails_when_output_missing() -> None:
    test_class = create_www_common_s3_existence_tests()
    instance = test_class()
    outputs: Dict[str, str] = {}
    with pytest.raises(AssertionError):
        instance.test_bucket_name_output_exists(outputs)


def test_handle_ecr_error_repository_not_found() -> None:
    error = create_client_error("RepositoryNotFoundException")
    with pytest.raises(pytest.skip.Exception):
        handle_ecr_error(error, "ecr:ListImages", "my-repo")


def test_fails_on_access_denied() -> None:
    error = create_client_error("AccessDeniedException")
    with pytest.raises(pytest.fail.Exception):
        handle_ecr_error(error, "ecr:ListImages", "my-repo")


def test_error_message_contains_operation() -> None:
    error = create_client_error("AccessDeniedException")
    with pytest.raises(pytest.fail.Exception, match="ecr:ListImages"):
        handle_ecr_error(error, "ecr:ListImages", "my-repo")


def test_error_message_contains_repository_name() -> None:
    error = create_client_error("AccessDeniedException")
    with pytest.raises(pytest.fail.Exception, match="my-repo"):
        handle_ecr_error(error, "ecr:ListImages", "my-repo")


def test_handle_ecr_error_other_errors() -> None:
    error = create_client_error("ServiceException")
    with pytest.raises(ClientError, match="ServiceException"):
        handle_ecr_error(error, "ecr:ListImages", "my-repo")


def test_create_log_group_configuration_tests_returns_class() -> None:
    test_class = create_log_group_configuration_tests("log_group_fixture")
    assert isinstance(test_class, type)


def test_create_log_group_configuration_tests_returns_class_with_name() -> None:
    test_class = create_log_group_configuration_tests("log_group_fixture")
    assert test_class.__name__ == "TestCloudWatchLogsConfiguration"


def test_has_test_handler_log_group_has_retention_set() -> None:
    test_class = create_log_group_configuration_tests("log_group_fixture")
    assert hasattr(test_class, "test_handler_log_group_has_retention_set")


def test_has_test_handler_log_group_retention_is_expected() -> None:
    test_class = create_log_group_configuration_tests("log_group_fixture")
    assert hasattr(test_class, "test_handler_log_group_retention_is_expected")


def test_create_lambda_role_existence_test_returns_callable() -> None:
    test_func = create_lambda_role_existence_test("role_name_fixture", "terraform/path")
    assert callable(test_func)


def test_create_lambda_role_existence_test_returns_function_with_name() -> None:
    test_func = create_lambda_role_existence_test("role_name_fixture", "terraform/path")
    assert test_func.__name__ == "test_lambda_execution_role_exists"


def test_create_kms_policy_test_returns_callable() -> None:
    test_func = create_kms_policy_test("role_name_fixture")
    assert callable(test_func)


def test_create_kms_policy_test_returns_function_with_name() -> None:
    test_func = create_kms_policy_test("role_name_fixture")
    assert test_func.__name__ == "test_lambda_role_has_kms_policy"


def test_s3_bucket_exists_success() -> None:
    test_class = create_www_common_s3_existence_tests()
    instance = test_class()
    mock_client = MagicMock()
    mock_client.head_bucket.return_value = {}
    outputs = {"bucket_name": "my-bucket"}
    instance.test_s3_bucket_exists(mock_client, outputs)
    assert mock_client.head_bucket.called


def test_s3_bucket_exists_skips_when_no_output() -> None:
    test_class = create_www_common_s3_existence_tests()
    instance = test_class()
    mock_client = MagicMock()
    outputs: Dict[str, str] = {}
    with pytest.raises(pytest.skip.Exception):
        instance.test_s3_bucket_exists(mock_client, outputs)


def test_s3_bucket_exists_fails_on_404() -> None:
    test_class = create_www_common_s3_existence_tests()
    instance = test_class()
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("404")
    outputs = {"bucket_name": "my-bucket"}
    with pytest.raises(AssertionError):
        instance.test_s3_bucket_exists(mock_client, outputs)


def test_s3_bucket_exists_reraises_other_errors() -> None:
    test_class = create_www_common_s3_existence_tests()
    instance = test_class()
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("500")
    outputs = {"bucket_name": "my-bucket"}
    with pytest.raises(AssertionError):
        instance.test_s3_bucket_exists(mock_client, outputs)


def test_log_group_has_retention_set_success() -> None:
    test_class = create_log_group_configuration_tests("log_group_fixture")
    instance = test_class()
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = {"name": "/aws/lambda/my-func", "retention": 7}
    instance.test_handler_log_group_has_retention_set(mock_request)
    assert mock_request.getfixturevalue.called


def test_log_group_has_retention_set_fails_when_none() -> None:
    test_class = create_log_group_configuration_tests("log_group_fixture")
    instance = test_class()
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = {
        "name": "/aws/lambda/my-func", "retention": None
    }
    with pytest.raises(AssertionError):
        instance.test_handler_log_group_has_retention_set(mock_request)


def test_log_group_retention_is_expected_success() -> None:
    test_class = create_log_group_configuration_tests("log_group_fixture", expected_retention=7)
    instance = test_class()
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = {"name": "/aws/lambda/my-func", "retention": 7}
    instance.test_handler_log_group_retention_is_expected(mock_request)
    assert mock_request.getfixturevalue.called


def test_log_group_retention_is_expected_fails_when_different() -> None:
    test_class = create_log_group_configuration_tests("log_group_fixture", expected_retention=7)
    instance = test_class()
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = {"name": "/aws/lambda/my-func", "retention": 30}
    with pytest.raises(AssertionError):
        instance.test_handler_log_group_retention_is_expected(mock_request)


def test_lambda_execution_role_exists_calls_helper() -> None:
    test_func = create_lambda_role_existence_test("role_name_fixture", "terraform/path")
    mock_client = MagicMock()
    mock_client.get_role.return_value = {"Role": {"RoleName": "my-role"}}
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = "my-role"
    assert test_func(None, mock_client, mock_request) is None
    mock_client.get_role.assert_called_once_with(RoleName="my-role")


def test_lambda_execution_role_exists_fails_when_role_missing() -> None:
    test_func = create_lambda_role_existence_test("role_name_fixture", "terraform/path")
    mock_client = MagicMock()
    mock_client.get_role.side_effect = create_client_error("NoSuchEntity")
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = "my-role"
    with pytest.raises(AssertionError):
        test_func(None, mock_client, mock_request)


def test_lambda_role_has_kms_policy_calls_helper() -> None:
    test_func = create_kms_policy_test("role_name_fixture")
    mock_client = MagicMock()
    mock_client.list_role_policies.return_value = {
        "PolicyNames": ["KMSDecrypt"]
    }
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = "my-role"
    assert test_func(None, mock_client, mock_request) is None


def test_lambda_role_has_kms_policy_fails_when_policy_missing() -> None:
    test_func = create_kms_policy_test("role_name_fixture")
    mock_client = MagicMock()
    mock_client.list_role_policies.return_value = {
        "PolicyNames": ["OtherPolicy"]
    }
    mock_request = MagicMock()
    mock_request.getfixturevalue.return_value = "my-role"
    with pytest.raises(AssertionError):
        test_func(None, mock_client, mock_request)
