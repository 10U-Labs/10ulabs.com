from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from boto_mocks import create_client_error
from test_fixtures.integration.helpers import (
    NO_CREDENTIALS_MESSAGE,
    assert_api_gateway_exists,
    aws_call_error,
    check_service_can_assume_role,
    check_state_file_readable,
    get_aws_account_id_via_cli,
    handle_ecr_authorization_error,
    iam_role_problem,
    lambda_function_problem,
    role_policy_problem,
    s3_head_bucket_problem,
    skip_if_api_gateway_unavailable,
)
from test_fixtures.outcomes import accepted


def test_no_problem_when_function_exists() -> None:
    mock_client = MagicMock()
    mock_client.get_function.return_value = {
        "Configuration": {"FunctionName": "MyFunction"}
    }
    assert lambda_function_problem(mock_client, "MyFunction", "terraform/path") == ""


def test_calls_get_function_with_function_name() -> None:
    mock_client = MagicMock()
    mock_client.get_function.return_value = {
        "Configuration": {"FunctionName": "MyFunction"}
    }
    lambda_function_problem(mock_client, "MyFunction", "terraform/path")
    assert mock_client.get_function.call_args[1]["FunctionName"] == "MyFunction"


def test_reports_resource_not_found_error() -> None:
    mock_client = MagicMock()
    mock_client.get_function.side_effect = create_client_error(
        "ResourceNotFoundException"
    )
    assert lambda_function_problem(mock_client, "MyFunction", "terraform/path")


def test_problem_contains_function_name() -> None:
    mock_client = MagicMock()
    mock_client.get_function.side_effect = create_client_error(
        "ResourceNotFoundException"
    )
    assert "MyFunction" in lambda_function_problem(
        mock_client, "MyFunction", "terraform/path"
    )


def test_lambda_function_problem_contains_terraform_path() -> None:
    mock_client = MagicMock()
    mock_client.get_function.side_effect = create_client_error(
        "ResourceNotFoundException"
    )
    assert "custom/path" in lambda_function_problem(
        mock_client, "MyFunction", "custom/path"
    )


def test_lambda_function_problem_other_errors() -> None:
    mock_client = MagicMock()
    mock_client.get_function.side_effect = create_client_error("AccessDenied")
    with pytest.raises(ClientError, match="AccessDenied"):
        lambda_function_problem(mock_client, "MyFunction", "terraform/path")


def test_no_problem_when_role_exists() -> None:
    mock_client = MagicMock()
    mock_client.get_role.return_value = {"Role": {"RoleName": "MyRole"}}
    assert iam_role_problem(mock_client, "MyRole", "terraform/path") == ""


def test_calls_get_role_with_role_name() -> None:
    mock_client = MagicMock()
    mock_client.get_role.return_value = {"Role": {"RoleName": "MyRole"}}
    iam_role_problem(mock_client, "MyRole", "terraform/path")
    assert mock_client.get_role.call_args[1]["RoleName"] == "MyRole"


def test_reports_no_such_entity_error() -> None:
    mock_client = MagicMock()
    mock_client.get_role.side_effect = create_client_error("NoSuchEntity")
    assert iam_role_problem(mock_client, "MyRole", "terraform/path")


def test_problem_contains_role_name() -> None:
    mock_client = MagicMock()
    mock_client.get_role.side_effect = create_client_error("NoSuchEntity")
    assert "MyRole" in iam_role_problem(mock_client, "MyRole", "terraform/path")


def test_iam_role_problem_other_errors() -> None:
    mock_client = MagicMock()
    mock_client.get_role.side_effect = create_client_error("AccessDenied")
    with pytest.raises(ClientError, match="AccessDenied"):
        iam_role_problem(mock_client, "MyRole", "terraform/path")


def test_no_problem_when_policy_exists() -> None:
    mock_client = MagicMock()
    mock_client.list_role_policies.return_value = {
        "PolicyNames": ["MyPolicy", "OtherPolicy"]
    }
    assert role_policy_problem(mock_client, "MyRole", "MyPolicy") == ""


def test_calls_list_role_policies_with_role_name() -> None:
    mock_client = MagicMock()
    mock_client.list_role_policies.return_value = {"PolicyNames": ["MyPolicy"]}
    role_policy_problem(mock_client, "MyRole", "MyPolicy")
    assert mock_client.list_role_policies.call_args[1]["RoleName"] == "MyRole"


def test_reports_when_policy_missing() -> None:
    mock_client = MagicMock()
    mock_client.list_role_policies.return_value = {"PolicyNames": ["OtherPolicy"]}
    assert role_policy_problem(mock_client, "MyRole", "MyPolicy")


def test_problem_contains_policy_name() -> None:
    mock_client = MagicMock()
    mock_client.list_role_policies.return_value = {"PolicyNames": []}
    assert "MissingPolicy" in role_policy_problem(
        mock_client, "MyRole", "MissingPolicy"
    )


def test_role_policy_problem_role_not_found() -> None:
    mock_client = MagicMock()
    mock_client.list_role_policies.side_effect = create_client_error("NoSuchEntity")
    with pytest.raises(pytest.skip.Exception):
        role_policy_problem(mock_client, "MyRole", "MyPolicy")


def test_role_policy_problem_other_errors() -> None:
    mock_client = MagicMock()
    mock_client.list_role_policies.side_effect = create_client_error("AccessDenied")
    with pytest.raises(ClientError, match="AccessDenied"):
        role_policy_problem(mock_client, "MyRole", "MyPolicy")


def test_returns_true_when_service_allowed() -> None:
    trust_policy = {
        "Statement": [
            {"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}}
        ]
    }
    result = check_service_can_assume_role(trust_policy, "lambda.amazonaws.com")
    assert result is True


def test_returns_true_with_service_list() -> None:
    trust_policy = {
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": ["lambda.amazonaws.com", "ecs.amazonaws.com"]
                },
            }
        ]
    }
    result = check_service_can_assume_role(trust_policy, "ecs.amazonaws.com")
    assert result is True


def test_returns_false_when_service_not_in_policy() -> None:
    trust_policy = {
        "Statement": [
            {"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}}
        ]
    }
    result = check_service_can_assume_role(trust_policy, "ecs.amazonaws.com")
    assert result is False


def test_returns_false_with_deny_effect() -> None:
    trust_policy = {
        "Statement": [
            {"Effect": "Deny", "Principal": {"Service": "lambda.amazonaws.com"}}
        ]
    }
    result = check_service_can_assume_role(trust_policy, "lambda.amazonaws.com")
    assert result is False


def test_returns_false_with_empty_statements() -> None:
    trust_policy: Dict[str, Any] = {"Statement": []}
    result = check_service_can_assume_role(trust_policy, "lambda.amazonaws.com")
    assert result is False


def test_returns_false_with_no_statements() -> None:
    trust_policy: Dict[str, Any] = {}
    result = check_service_can_assume_role(trust_policy, "lambda.amazonaws.com")
    assert result is False


@patch("test_fixtures.integration.helpers.subprocess.run")
def test_returns_account_id_on_success(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="123456789012\n")
    result = get_aws_account_id_via_cli()
    assert result == "123456789012"


@patch("test_fixtures.integration.helpers.subprocess.run")
def test_strips_whitespace_from_output(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="  123456789012  \n")
    result = get_aws_account_id_via_cli()
    assert result == "123456789012"


@patch("test_fixtures.integration.helpers.subprocess.run")
def test_calls_aws_command(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="123456789012")
    get_aws_account_id_via_cli()
    call_args = mock_run.call_args[0][0]
    assert "aws" in call_args


@patch("test_fixtures.integration.helpers.subprocess.run")
def test_calls_sts_service(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="123456789012")
    get_aws_account_id_via_cli()
    call_args = mock_run.call_args[0][0]
    assert "sts" in call_args


@patch("test_fixtures.integration.helpers.subprocess.run")
def test_calls_get_caller_identity_action(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="123456789012")
    get_aws_account_id_via_cli()
    call_args = mock_run.call_args[0][0]
    assert "get-caller-identity" in call_args


@patch("test_fixtures.integration.helpers.subprocess.run")
def test_get_aws_account_id_via_cli_failure(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=1, stdout="")
    result = get_aws_account_id_via_cli()
    assert result == ""


def test_fails_on_access_denied() -> None:
    error = create_client_error("AccessDeniedException")
    with pytest.raises(pytest.fail.Exception):
        handle_ecr_authorization_error(
            error, "ecr:DescribeRepositories", "my-repo"
        )


def test_error_message_contains_operation() -> None:
    error = create_client_error("AccessDeniedException")
    with pytest.raises(pytest.fail.Exception, match="ecr:DescribeRepositories"):
        handle_ecr_authorization_error(
            error, "ecr:DescribeRepositories", "my-repo"
        )


def test_error_message_contains_repository_name() -> None:
    error = create_client_error("AccessDeniedException")
    with pytest.raises(pytest.fail.Exception, match="my-repo"):
        handle_ecr_authorization_error(
            error, "ecr:DescribeRepositories", "my-repo"
        )


def test_handle_ecr_authorization_error_repository_not_found() -> None:
    error = create_client_error("RepositoryNotFoundException")
    assert accepted(handle_ecr_authorization_error, error, "ecr:DescribeRepositories", "my-repo")


def test_handle_ecr_authorization_error_other_errors() -> None:
    error = create_client_error("ServiceException")
    with pytest.raises(ClientError, match="ServiceException"):
        handle_ecr_authorization_error(error, "ecr:DescribeRepositories", "my-repo")


def test_no_problem_when_bucket_accessible() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.return_value = {}
    assert s3_head_bucket_problem(mock_client, "my-bucket") == ""


def test_calls_head_bucket_with_bucket_name() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.return_value = {}
    s3_head_bucket_problem(mock_client, "my-bucket")
    assert mock_client.head_bucket.call_args[1]["Bucket"] == "my-bucket"


def test_s3_head_bucket_problem_reports_403_error() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("403")
    assert s3_head_bucket_problem(mock_client, "my-bucket")


def test_reports_access_denied_error() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("AccessDenied")
    assert s3_head_bucket_problem(mock_client, "my-bucket")


def test_problem_contains_bucket_name() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("403")
    assert "my-bucket" in s3_head_bucket_problem(mock_client, "my-bucket")


def test_s3_head_bucket_problem_bucket_not_found() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("404")
    assert s3_head_bucket_problem(mock_client, "my-bucket") == ""


def test_s3_head_bucket_problem_other_errors() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("ServiceException")
    with pytest.raises(ClientError, match="ServiceException"):
        s3_head_bucket_problem(mock_client, "my-bucket")


def test_aws_call_error_empty_when_call_succeeds() -> None:
    mock_client = MagicMock()
    mock_client.list_buckets.return_value = {}
    assert aws_call_error(mock_client.list_buckets) == ""


def test_aws_call_error_names_the_error_code() -> None:
    mock_client = MagicMock()
    mock_client.list_buckets.side_effect = create_client_error("AccessDenied")
    assert "AccessDenied" in aws_call_error(mock_client.list_buckets)


def test_aws_call_error_carries_the_error_message() -> None:
    mock_client = MagicMock()
    mock_client.list_buckets.side_effect = create_client_error(
        "AccessDenied", message="no soup for you"
    )
    assert "no soup for you" in aws_call_error(mock_client.list_buckets)


def test_aws_call_error_empty_for_a_tolerated_code() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("404")
    assert aws_call_error(mock_client.head_bucket, "404") == ""


def test_aws_call_error_reports_an_untolerated_code() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("403")
    assert aws_call_error(mock_client.head_bucket, "404")


def test_skip_if_api_gateway_unavailable_available() -> None:
    api_gateway_info = {"id": "abc123", "exists": True}
    assert accepted(skip_if_api_gateway_unavailable, api_gateway_info)


def test_skip_if_api_gateway_unavailable_no_id() -> None:
    api_gateway_info = {"id": None, "exists": False}
    with pytest.raises(pytest.skip.Exception):
        skip_if_api_gateway_unavailable(api_gateway_info)


def test_skip_if_api_gateway_unavailable_does_not_exist() -> None:
    api_gateway_info = {"id": "abc123", "exists": False}
    with pytest.raises(pytest.skip.Exception):
        skip_if_api_gateway_unavailable(api_gateway_info)


def test_does_not_raise_when_file_readable() -> None:
    mock_client = MagicMock()
    mock_client.head_object.return_value = {}
    check_state_file_readable(
                mock_client, "my-bucket", "state/terraform.tfstate"
            )
    assert mock_client.head_object.called


def test_calls_head_object_with_bucket_and_key() -> None:
    mock_client = MagicMock()
    mock_client.head_object.return_value = {}
    check_state_file_readable(mock_client, "my-bucket", "state/terraform.tfstate")
    assert mock_client.head_object.call_args[1]["Bucket"] == "my-bucket"


def test_check_state_file_readable_fails_on_403_error() -> None:
    mock_client = MagicMock()
    mock_client.head_object.side_effect = create_client_error("403")
    with pytest.raises(pytest.fail.Exception):
        check_state_file_readable(
            mock_client, "my-bucket", "state/terraform.tfstate"
        )


def test_error_message_contains_state_key() -> None:
    mock_client = MagicMock()
    mock_client.head_object.side_effect = create_client_error("403")
    with pytest.raises(pytest.fail.Exception, match="state/terraform.tfstate"):
        check_state_file_readable(
            mock_client, "my-bucket", "state/terraform.tfstate"
        )


def test_check_state_file_readable_not_found() -> None:
    mock_client = MagicMock()
    mock_client.head_object.side_effect = create_client_error("404")
    with pytest.raises(pytest.skip.Exception):
        check_state_file_readable(
            mock_client, "my-bucket", "state/terraform.tfstate"
        )


def test_check_state_file_readable_other_errors() -> None:
    mock_client = MagicMock()
    mock_client.head_object.side_effect = create_client_error("ServiceException")
    with pytest.raises(ClientError, match="ServiceException"):
        check_state_file_readable(
            mock_client, "my-bucket", "state/terraform.tfstate"
        )


def test_assert_api_gateway_exists_success() -> None:
    api_gateway_info = {"id": "abc123", "exists": True}
    assert accepted(assert_api_gateway_exists, api_gateway_info)


def test_assert_api_gateway_exists_no_id() -> None:
    api_gateway_info = {"id": None, "exists": False}
    with pytest.raises(pytest.skip.Exception):
        assert_api_gateway_exists(api_gateway_info)


def test_raises_assertion_when_api_does_not_exist() -> None:
    api_gateway_info = {"id": "abc123", "exists": False}
    with pytest.raises(AssertionError):
        assert_api_gateway_exists(api_gateway_info)


def test_error_message_contains_api_id() -> None:
    api_gateway_info = {"id": "abc123xyz", "exists": False}
    with pytest.raises(AssertionError, match="abc123xyz"):
        assert_api_gateway_exists(api_gateway_info)


def test_assert_api_gateway_exists_error_message_contains_terraform_path() -> None:
    api_gateway_info = {"id": "abc123", "exists": False}
    with pytest.raises(AssertionError, match="custom/terraform/path"):
        assert_api_gateway_exists(api_gateway_info, "custom/terraform/path")


def test_message_contains_aws() -> None:
    assert "AWS" in NO_CREDENTIALS_MESSAGE


def test_message_contains_credentials() -> None:
    assert "credentials" in NO_CREDENTIALS_MESSAGE
