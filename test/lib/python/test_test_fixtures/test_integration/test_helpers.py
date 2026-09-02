from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from boto_mocks import create_client_error
from test_fixtures.integration.helpers import (
    NO_CREDENTIALS_MESSAGE,
    assert_api_gateway_exists,
    check_iam_role_exists,
    check_lambda_function_exists,
    check_lambda_role_has_policy,
    check_s3_head_bucket_permission,
    check_service_can_assume_role,
    check_state_file_readable,
    get_aws_account_id_via_cli,
    handle_ecr_authorization_error,
    skip_if_api_gateway_unavailable,
)


class TestCheckLambdaFunctionExistsSuccess:
    def test_does_not_raise_when_function_exists(self) -> None:
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"FunctionName": "MyFunction"}
        }
        assert check_lambda_function_exists(mock_client, "MyFunction", "terraform/path") is None

    def test_calls_get_function_with_function_name(self) -> None:
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"FunctionName": "MyFunction"}
        }
        check_lambda_function_exists(mock_client, "MyFunction", "terraform/path")
        assert mock_client.get_function.call_args[1]["FunctionName"] == "MyFunction"


class TestCheckLambdaFunctionExistsNotFound:
    def test_fails_with_resource_not_found_error(self) -> None:
        mock_client = MagicMock()
        mock_client.get_function.side_effect = create_client_error(
            "ResourceNotFoundException"
        )
        with pytest.raises(pytest.fail.Exception):
            check_lambda_function_exists(mock_client, "MyFunction", "terraform/path")

    def test_error_message_contains_function_name(self) -> None:
        mock_client = MagicMock()
        mock_client.get_function.side_effect = create_client_error(
            "ResourceNotFoundException"
        )
        with pytest.raises(pytest.fail.Exception, match="MyFunction"):
            check_lambda_function_exists(mock_client, "MyFunction", "terraform/path")

    def test_error_message_contains_terraform_path(self) -> None:
        mock_client = MagicMock()
        mock_client.get_function.side_effect = create_client_error(
            "ResourceNotFoundException"
        )
        with pytest.raises(pytest.fail.Exception, match="custom/path"):
            check_lambda_function_exists(mock_client, "MyFunction", "custom/path")


def test_check_lambda_function_exists_other_errors() -> None:
    mock_client = MagicMock()
    mock_client.get_function.side_effect = create_client_error("AccessDenied")
    with pytest.raises(ClientError, match="AccessDenied"):
        check_lambda_function_exists(mock_client, "MyFunction", "terraform/path")


class TestCheckIAMRoleExistsSuccess:
    def test_does_not_raise_when_role_exists(self) -> None:
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyRole"}}
        assert check_iam_role_exists(mock_client, "MyRole", "terraform/path") is None

    def test_calls_get_role_with_role_name(self) -> None:
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyRole"}}
        check_iam_role_exists(mock_client, "MyRole", "terraform/path")
        assert mock_client.get_role.call_args[1]["RoleName"] == "MyRole"


class TestCheckIAMRoleExistsNotFound:
    def test_fails_with_no_such_entity_error(self) -> None:
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("NoSuchEntity")
        with pytest.raises(pytest.fail.Exception):
            check_iam_role_exists(mock_client, "MyRole", "terraform/path")

    def test_error_message_contains_role_name(self) -> None:
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("NoSuchEntity")
        with pytest.raises(pytest.fail.Exception, match="MyRole"):
            check_iam_role_exists(mock_client, "MyRole", "terraform/path")


def test_check_iam_role_exists_other_errors() -> None:
    mock_client = MagicMock()
    mock_client.get_role.side_effect = create_client_error("AccessDenied")
    with pytest.raises(ClientError, match="AccessDenied"):
        check_iam_role_exists(mock_client, "MyRole", "terraform/path")


class TestCheckLambdaRoleHasPolicySuccess:
    def test_does_not_raise_when_policy_exists(self) -> None:
        mock_client = MagicMock()
        mock_client.list_role_policies.return_value = {
            "PolicyNames": ["MyPolicy", "OtherPolicy"]
        }
        assert check_lambda_role_has_policy(mock_client, "MyRole", "MyPolicy") is None

    def test_calls_list_role_policies_with_role_name(self) -> None:
        mock_client = MagicMock()
        mock_client.list_role_policies.return_value = {"PolicyNames": ["MyPolicy"]}
        check_lambda_role_has_policy(mock_client, "MyRole", "MyPolicy")
        assert mock_client.list_role_policies.call_args[1]["RoleName"] == "MyRole"


class TestCheckLambdaRoleHasPolicyMissing:
    def test_raises_assertion_error_when_policy_missing(self) -> None:
        mock_client = MagicMock()
        mock_client.list_role_policies.return_value = {"PolicyNames": ["OtherPolicy"]}
        with pytest.raises(AssertionError):
            check_lambda_role_has_policy(mock_client, "MyRole", "MyPolicy")

    def test_error_message_contains_policy_name(self) -> None:
        mock_client = MagicMock()
        mock_client.list_role_policies.return_value = {"PolicyNames": []}
        with pytest.raises(AssertionError, match="MissingPolicy"):
            check_lambda_role_has_policy(mock_client, "MyRole", "MissingPolicy")


def test_check_lambda_role_has_policy_role_not_found() -> None:
    mock_client = MagicMock()
    mock_client.list_role_policies.side_effect = create_client_error("NoSuchEntity")
    with pytest.raises(pytest.skip.Exception):
        check_lambda_role_has_policy(mock_client, "MyRole", "MyPolicy")


def test_check_lambda_role_has_policy_other_errors() -> None:
    mock_client = MagicMock()
    mock_client.list_role_policies.side_effect = create_client_error("AccessDenied")
    with pytest.raises(ClientError, match="AccessDenied"):
        check_lambda_role_has_policy(mock_client, "MyRole", "MyPolicy")


class TestCheckServiceCanAssumeRoleAllowed:
    def test_returns_true_when_service_allowed(self) -> None:
        trust_policy = {
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}}
            ]
        }
        result = check_service_can_assume_role(trust_policy, "lambda.amazonaws.com")
        assert result is True

    def test_returns_true_with_service_list(self) -> None:
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


class TestCheckServiceCanAssumeRoleNotAllowed:
    def test_returns_false_when_service_not_in_policy(self) -> None:
        trust_policy = {
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}}
            ]
        }
        result = check_service_can_assume_role(trust_policy, "ecs.amazonaws.com")
        assert result is False

    def test_returns_false_with_deny_effect(self) -> None:
        trust_policy = {
            "Statement": [
                {"Effect": "Deny", "Principal": {"Service": "lambda.amazonaws.com"}}
            ]
        }
        result = check_service_can_assume_role(trust_policy, "lambda.amazonaws.com")
        assert result is False


class TestCheckServiceCanAssumeRoleEmptyPolicy:
    def test_returns_false_with_empty_statements(self) -> None:
        trust_policy: Dict[str, Any] = {"Statement": []}
        result = check_service_can_assume_role(trust_policy, "lambda.amazonaws.com")
        assert result is False

    def test_returns_false_with_no_statements(self) -> None:
        trust_policy: Dict[str, Any] = {}
        result = check_service_can_assume_role(trust_policy, "lambda.amazonaws.com")
        assert result is False


class TestGetAWSAccountIdViaCLISuccess:
    @patch("test_fixtures.integration.helpers.subprocess.run")
    def test_returns_account_id_on_success(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="123456789012\n")
        result = get_aws_account_id_via_cli()
        assert result == "123456789012"

    @patch("test_fixtures.integration.helpers.subprocess.run")
    def test_strips_whitespace_from_output(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="  123456789012  \n")
        result = get_aws_account_id_via_cli()
        assert result == "123456789012"

    @patch("test_fixtures.integration.helpers.subprocess.run")
    def test_calls_aws_command(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="123456789012")
        get_aws_account_id_via_cli()
        call_args = mock_run.call_args[0][0]
        assert "aws" in call_args

    @patch("test_fixtures.integration.helpers.subprocess.run")
    def test_calls_sts_service(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="123456789012")
        get_aws_account_id_via_cli()
        call_args = mock_run.call_args[0][0]
        assert "sts" in call_args

    @patch("test_fixtures.integration.helpers.subprocess.run")
    def test_calls_get_caller_identity_action(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="123456789012")
        get_aws_account_id_via_cli()
        call_args = mock_run.call_args[0][0]
        assert "get-caller-identity" in call_args


@patch("test_fixtures.integration.helpers.subprocess.run")
def test_get_aws_account_id_via_cli_failure(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=1, stdout="")
    result = get_aws_account_id_via_cli()
    assert result == ""


class TestHandleECRAuthorizationErrorAccessDenied:
    def test_fails_on_access_denied(self) -> None:
        error = create_client_error("AccessDeniedException")
        with pytest.raises(pytest.fail.Exception):
            handle_ecr_authorization_error(
                error, "ecr:DescribeRepositories", "my-repo"
            )

    def test_error_message_contains_operation(self) -> None:
        error = create_client_error("AccessDeniedException")
        with pytest.raises(pytest.fail.Exception, match="ecr:DescribeRepositories"):
            handle_ecr_authorization_error(
                error, "ecr:DescribeRepositories", "my-repo"
            )

    def test_error_message_contains_repository_name(self) -> None:
        error = create_client_error("AccessDeniedException")
        with pytest.raises(pytest.fail.Exception, match="my-repo"):
            handle_ecr_authorization_error(
                error, "ecr:DescribeRepositories", "my-repo"
            )


def test_handle_ecr_authorization_error_repository_not_found() -> None:
    error = create_client_error("RepositoryNotFoundException")
    assert handle_ecr_authorization_error(error, "ecr:DescribeRepositories", "my-repo") is None


def test_handle_ecr_authorization_error_other_errors() -> None:
    error = create_client_error("ServiceException")
    with pytest.raises(ClientError, match="ServiceException"):
        handle_ecr_authorization_error(error, "ecr:DescribeRepositories", "my-repo")


class TestCheckS3HeadBucketPermissionSuccess:
    def test_does_not_raise_when_bucket_accessible(self) -> None:
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = {}
        assert check_s3_head_bucket_permission(mock_client, "my-bucket") is None

    def test_calls_head_bucket_with_bucket_name(self) -> None:
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = {}
        check_s3_head_bucket_permission(mock_client, "my-bucket")
        assert mock_client.head_bucket.call_args[1]["Bucket"] == "my-bucket"


class TestCheckS3HeadBucketPermissionAccessDenied:
    def test_fails_on_403_error(self) -> None:
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("403")
        with pytest.raises(pytest.fail.Exception):
            check_s3_head_bucket_permission(mock_client, "my-bucket")

    def test_fails_on_access_denied_error(self) -> None:
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            check_s3_head_bucket_permission(mock_client, "my-bucket")

    def test_error_message_contains_bucket_name(self) -> None:
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("403")
        with pytest.raises(pytest.fail.Exception, match="my-bucket"):
            check_s3_head_bucket_permission(mock_client, "my-bucket")


def test_check_s3_head_bucket_permission_bucket_not_found() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("404")
    assert check_s3_head_bucket_permission(mock_client, "my-bucket") is None


def test_check_s3_head_bucket_permission_other_errors() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("ServiceException")
    with pytest.raises(ClientError, match="ServiceException"):
        check_s3_head_bucket_permission(mock_client, "my-bucket")


def test_skip_if_api_gateway_unavailable_available() -> None:
    api_gateway_info = {"id": "abc123", "exists": True}
    assert skip_if_api_gateway_unavailable(api_gateway_info) is None


def test_skip_if_api_gateway_unavailable_no_id() -> None:
    api_gateway_info = {"id": None, "exists": False}
    with pytest.raises(pytest.skip.Exception):
        skip_if_api_gateway_unavailable(api_gateway_info)


def test_skip_if_api_gateway_unavailable_does_not_exist() -> None:
    api_gateway_info = {"id": "abc123", "exists": False}
    with pytest.raises(pytest.skip.Exception):
        skip_if_api_gateway_unavailable(api_gateway_info)


class TestCheckStateFileReadableSuccess:
    def test_does_not_raise_when_file_readable(self) -> None:
        mock_client = MagicMock()
        mock_client.head_object.return_value = {}
        assert check_state_file_readable(
            mock_client, "my-bucket", "state/terraform.tfstate"
        ) is None

    def test_calls_head_object_with_bucket_and_key(self) -> None:
        mock_client = MagicMock()
        mock_client.head_object.return_value = {}
        check_state_file_readable(mock_client, "my-bucket", "state/terraform.tfstate")
        assert mock_client.head_object.call_args[1]["Bucket"] == "my-bucket"


class TestCheckStateFileReadableAccessDenied:
    def test_fails_on_403_error(self) -> None:
        mock_client = MagicMock()
        mock_client.head_object.side_effect = create_client_error("403")
        with pytest.raises(pytest.fail.Exception):
            check_state_file_readable(
                mock_client, "my-bucket", "state/terraform.tfstate"
            )

    def test_error_message_contains_state_key(self) -> None:
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
    assert assert_api_gateway_exists(api_gateway_info) is None


def test_assert_api_gateway_exists_no_id() -> None:
    api_gateway_info = {"id": None, "exists": False}
    with pytest.raises(pytest.skip.Exception):
        assert_api_gateway_exists(api_gateway_info)


class TestAssertAPIGatewayExistsDoesNotExist:
    def test_raises_assertion_when_api_does_not_exist(self) -> None:
        api_gateway_info = {"id": "abc123", "exists": False}
        with pytest.raises(AssertionError):
            assert_api_gateway_exists(api_gateway_info)

    def test_error_message_contains_api_id(self) -> None:
        api_gateway_info = {"id": "abc123xyz", "exists": False}
        with pytest.raises(AssertionError, match="abc123xyz"):
            assert_api_gateway_exists(api_gateway_info)

    def test_error_message_contains_terraform_path(self) -> None:
        api_gateway_info = {"id": "abc123", "exists": False}
        with pytest.raises(AssertionError, match="custom/terraform/path"):
            assert_api_gateway_exists(api_gateway_info, "custom/terraform/path")


class TestNoCredentialsMessage:
    def test_message_contains_aws(self) -> None:
        assert "AWS" in NO_CREDENTIALS_MESSAGE

    def test_message_contains_credentials(self) -> None:
        assert "credentials" in NO_CREDENTIALS_MESSAGE
