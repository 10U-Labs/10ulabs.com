"""Unit tests for test_fixtures.integration.helpers module."""
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError, NoCredentialsError

from test_fixtures.integration.helpers import (
    NO_CREDENTIALS_MESSAGE,
    assert_api_gateway_exists,
    assert_iam_role_name_is_pascalcase,
    check_credentials_available,
    check_credentials_valid,
    check_iam_role_exists,
    check_lambda_function_exists,
    check_lambda_role_has_policy,
    check_s3_head_bucket_permission,
    check_service_can_assume_role,
    check_state_file_readable,
    fail_no_credentials,
    get_aws_account_id_via_cli,
    handle_ecr_authorization_error,
    skip_if_api_gateway_unavailable,
)


def _create_client_error(code: str, message: str = "Test error") -> ClientError:
    """Create a ClientError for testing."""
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "TestOperation"
    )


# === check_lambda_function_exists ===


class TestCheckLambdaFunctionExistsSuccess:
    """Tests for check_lambda_function_exists when function exists."""

    def test_does_not_raise_when_function_exists(self):
        """check_lambda_function_exists does not raise when function exists."""
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"FunctionName": "MyFunction"}
        }
        result = check_lambda_function_exists(mock_client, "MyFunction", "terraform/path")
        assert result is None

    def test_calls_get_function_with_function_name(self):
        """check_lambda_function_exists calls get_function with function name."""
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {"FunctionName": "MyFunction"}
        }
        check_lambda_function_exists(mock_client, "MyFunction", "terraform/path")
        assert mock_client.get_function.call_args[1]["FunctionName"] == "MyFunction"


class TestCheckLambdaFunctionExistsNotFound:
    """Tests for check_lambda_function_exists when function not found."""

    def test_fails_with_resource_not_found_error(self):
        """check_lambda_function_exists fails with ResourceNotFoundException."""
        mock_client = MagicMock()
        mock_client.get_function.side_effect = _create_client_error(
            "ResourceNotFoundException"
        )
        with pytest.raises(pytest.fail.Exception):
            check_lambda_function_exists(mock_client, "MyFunction", "terraform/path")

    def test_error_message_contains_function_name(self):
        """check_lambda_function_exists error contains function name."""
        mock_client = MagicMock()
        mock_client.get_function.side_effect = _create_client_error(
            "ResourceNotFoundException"
        )
        with pytest.raises(pytest.fail.Exception, match="MyFunction"):
            check_lambda_function_exists(mock_client, "MyFunction", "terraform/path")

    def test_error_message_contains_terraform_path(self):
        """check_lambda_function_exists error contains terraform path."""
        mock_client = MagicMock()
        mock_client.get_function.side_effect = _create_client_error(
            "ResourceNotFoundException"
        )
        with pytest.raises(pytest.fail.Exception, match="custom/path"):
            check_lambda_function_exists(mock_client, "MyFunction", "custom/path")


class TestCheckLambdaFunctionExistsOtherErrors:
    """Tests for check_lambda_function_exists with other errors."""

    def test_reraises_other_client_errors(self):
        """check_lambda_function_exists reraises non-ResourceNotFoundException errors."""
        mock_client = MagicMock()
        mock_client.get_function.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(ClientError, match="AccessDenied"):
            check_lambda_function_exists(mock_client, "MyFunction", "terraform/path")


# === check_iam_role_exists ===


class TestCheckIAMRoleExistsSuccess:
    """Tests for check_iam_role_exists when role exists."""

    def test_does_not_raise_when_role_exists(self):
        """check_iam_role_exists does not raise when role exists."""
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyRole"}}
        result = check_iam_role_exists(mock_client, "MyRole", "terraform/path")
        assert result is None

    def test_calls_get_role_with_role_name(self):
        """check_iam_role_exists calls get_role with role name."""
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyRole"}}
        check_iam_role_exists(mock_client, "MyRole", "terraform/path")
        assert mock_client.get_role.call_args[1]["RoleName"] == "MyRole"


class TestCheckIAMRoleExistsNotFound:
    """Tests for check_iam_role_exists when role not found."""

    def test_fails_with_no_such_entity_error(self):
        """check_iam_role_exists fails with NoSuchEntity."""
        mock_client = MagicMock()
        mock_client.get_role.side_effect = _create_client_error("NoSuchEntity")
        with pytest.raises(pytest.fail.Exception):
            check_iam_role_exists(mock_client, "MyRole", "terraform/path")

    def test_error_message_contains_role_name(self):
        """check_iam_role_exists error contains role name."""
        mock_client = MagicMock()
        mock_client.get_role.side_effect = _create_client_error("NoSuchEntity")
        with pytest.raises(pytest.fail.Exception, match="MyRole"):
            check_iam_role_exists(mock_client, "MyRole", "terraform/path")


class TestCheckIAMRoleExistsOtherErrors:
    """Tests for check_iam_role_exists with other errors."""

    def test_reraises_other_client_errors(self):
        """check_iam_role_exists reraises non-NoSuchEntity errors."""
        mock_client = MagicMock()
        mock_client.get_role.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(ClientError, match="AccessDenied"):
            check_iam_role_exists(mock_client, "MyRole", "terraform/path")


# === check_lambda_role_has_policy ===


class TestCheckLambdaRoleHasPolicySuccess:
    """Tests for check_lambda_role_has_policy when policy exists."""

    def test_does_not_raise_when_policy_exists(self):
        """check_lambda_role_has_policy does not raise when policy exists."""
        mock_client = MagicMock()
        mock_client.list_role_policies.return_value = {
            "PolicyNames": ["MyPolicy", "OtherPolicy"]
        }
        result = check_lambda_role_has_policy(mock_client, "MyRole", "MyPolicy")
        assert result is None

    def test_calls_list_role_policies_with_role_name(self):
        """check_lambda_role_has_policy calls list_role_policies with role name."""
        mock_client = MagicMock()
        mock_client.list_role_policies.return_value = {"PolicyNames": ["MyPolicy"]}
        check_lambda_role_has_policy(mock_client, "MyRole", "MyPolicy")
        assert mock_client.list_role_policies.call_args[1]["RoleName"] == "MyRole"


class TestCheckLambdaRoleHasPolicyMissing:
    """Tests for check_lambda_role_has_policy when policy is missing."""

    def test_raises_assertion_error_when_policy_missing(self):
        """check_lambda_role_has_policy raises AssertionError when policy missing."""
        mock_client = MagicMock()
        mock_client.list_role_policies.return_value = {"PolicyNames": ["OtherPolicy"]}
        with pytest.raises(AssertionError):
            check_lambda_role_has_policy(mock_client, "MyRole", "MyPolicy")

    def test_error_message_contains_policy_name(self):
        """check_lambda_role_has_policy error contains policy name."""
        mock_client = MagicMock()
        mock_client.list_role_policies.return_value = {"PolicyNames": []}
        with pytest.raises(AssertionError, match="MissingPolicy"):
            check_lambda_role_has_policy(mock_client, "MyRole", "MissingPolicy")


class TestCheckLambdaRoleHasPolicyRoleNotFound:
    """Tests for check_lambda_role_has_policy when role not found."""

    def test_skips_when_role_does_not_exist(self):
        """check_lambda_role_has_policy skips when role does not exist."""
        mock_client = MagicMock()
        mock_client.list_role_policies.side_effect = _create_client_error("NoSuchEntity")
        with pytest.raises(pytest.skip.Exception):
            check_lambda_role_has_policy(mock_client, "MyRole", "MyPolicy")


class TestCheckLambdaRoleHasPolicyOtherErrors:
    """Tests for check_lambda_role_has_policy with other errors."""

    def test_reraises_other_client_errors(self):
        """check_lambda_role_has_policy reraises non-NoSuchEntity errors."""
        mock_client = MagicMock()
        mock_client.list_role_policies.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(ClientError, match="AccessDenied"):
            check_lambda_role_has_policy(mock_client, "MyRole", "MyPolicy")


# === fail_no_credentials ===


class TestFailNoCredentials:
    """Tests for fail_no_credentials function."""

    def test_raises_pytest_fail(self):
        """fail_no_credentials raises pytest.fail.Exception."""
        with pytest.raises(pytest.fail.Exception):
            fail_no_credentials()

    def test_error_message_contains_credentials_message(self):
        """fail_no_credentials error contains NO_CREDENTIALS_MESSAGE."""
        with pytest.raises(pytest.fail.Exception, match="(?i)credentials"):
            fail_no_credentials()


# === check_credentials_available ===


class TestCheckCredentialsAvailableSuccess:
    """Tests for check_credentials_available when credentials available."""

    def test_does_not_raise_when_credentials_available(self):
        """check_credentials_available does not raise with valid credentials."""
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
        result = check_credentials_available(mock_client)
        assert result is None

    def test_calls_get_caller_identity(self):
        """check_credentials_available calls get_caller_identity."""
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
        check_credentials_available(mock_client)
        assert mock_client.get_caller_identity.call_count == 1


class TestCheckCredentialsAvailableNoCredentials:
    """Tests for check_credentials_available when no credentials."""

    def test_fails_when_no_credentials(self):
        """check_credentials_available fails with NoCredentialsError."""
        mock_client = MagicMock()
        mock_client.get_caller_identity.side_effect = NoCredentialsError()
        with pytest.raises(pytest.fail.Exception):
            check_credentials_available(mock_client)


# === check_credentials_valid ===


class TestCheckCredentialsValidSuccess:
    """Tests for check_credentials_valid when credentials valid."""

    def test_does_not_raise_when_credentials_valid(self):
        """check_credentials_valid does not raise with valid credentials."""
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
        result = check_credentials_valid(mock_client)
        assert result is None

    def test_calls_get_caller_identity(self):
        """check_credentials_valid calls get_caller_identity."""
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
        check_credentials_valid(mock_client)
        assert mock_client.get_caller_identity.call_count == 1


class TestCheckCredentialsValidInvalid:
    """Tests for check_credentials_valid when credentials invalid."""

    def test_fails_when_credentials_invalid(self):
        """check_credentials_valid fails with ClientError."""
        mock_client = MagicMock()
        mock_client.get_caller_identity.side_effect = _create_client_error(
            "ExpiredTokenException", "Token has expired"
        )
        with pytest.raises(pytest.fail.Exception):
            check_credentials_valid(mock_client)

    def test_error_message_contains_error_details(self):
        """check_credentials_valid error contains error details."""
        mock_client = MagicMock()
        mock_client.get_caller_identity.side_effect = _create_client_error(
            "ExpiredTokenException", "Token has expired"
        )
        with pytest.raises(pytest.fail.Exception, match="Token has expired"):
            check_credentials_valid(mock_client)


# === check_service_can_assume_role ===


class TestCheckServiceCanAssumeRoleAllowed:
    """Tests for check_service_can_assume_role when service is allowed."""

    def test_returns_true_when_service_allowed(self):
        """check_service_can_assume_role returns True when service allowed."""
        trust_policy = {
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}}
            ]
        }
        result = check_service_can_assume_role(trust_policy, "lambda.amazonaws.com")
        assert result is True

    def test_returns_true_with_service_list(self):
        """check_service_can_assume_role returns True with service list."""
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
    """Tests for check_service_can_assume_role when service is not allowed."""

    def test_returns_false_when_service_not_in_policy(self):
        """check_service_can_assume_role returns False when service not in policy."""
        trust_policy = {
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}}
            ]
        }
        result = check_service_can_assume_role(trust_policy, "ecs.amazonaws.com")
        assert result is False

    def test_returns_false_with_deny_effect(self):
        """check_service_can_assume_role returns False with Deny effect."""
        trust_policy = {
            "Statement": [
                {"Effect": "Deny", "Principal": {"Service": "lambda.amazonaws.com"}}
            ]
        }
        result = check_service_can_assume_role(trust_policy, "lambda.amazonaws.com")
        assert result is False


class TestCheckServiceCanAssumeRoleEmptyPolicy:
    """Tests for check_service_can_assume_role with empty policy."""

    def test_returns_false_with_empty_statements(self):
        """check_service_can_assume_role returns False with empty statements."""
        trust_policy = {"Statement": []}
        result = check_service_can_assume_role(trust_policy, "lambda.amazonaws.com")
        assert result is False

    def test_returns_false_with_no_statements(self):
        """check_service_can_assume_role returns False with no Statement key."""
        trust_policy = {}
        result = check_service_can_assume_role(trust_policy, "lambda.amazonaws.com")
        assert result is False


# === get_aws_account_id_via_cli ===


class TestGetAWSAccountIdViaCLISuccess:
    """Tests for get_aws_account_id_via_cli on success."""

    @patch("test_fixtures.integration.helpers.subprocess.run")
    def test_returns_account_id_on_success(self, mock_run):
        """get_aws_account_id_via_cli returns account ID on success."""
        mock_run.return_value = MagicMock(returncode=0, stdout="123456789012\n")
        result = get_aws_account_id_via_cli()
        assert result == "123456789012"

    @patch("test_fixtures.integration.helpers.subprocess.run")
    def test_strips_whitespace_from_output(self, mock_run):
        """get_aws_account_id_via_cli strips whitespace."""
        mock_run.return_value = MagicMock(returncode=0, stdout="  123456789012  \n")
        result = get_aws_account_id_via_cli()
        assert result == "123456789012"

    @patch("test_fixtures.integration.helpers.subprocess.run")
    def test_calls_aws_command(self, mock_run):
        """get_aws_account_id_via_cli calls aws command."""
        mock_run.return_value = MagicMock(returncode=0, stdout="123456789012")
        get_aws_account_id_via_cli()
        call_args = mock_run.call_args[0][0]
        assert "aws" in call_args

    @patch("test_fixtures.integration.helpers.subprocess.run")
    def test_calls_sts_service(self, mock_run):
        """get_aws_account_id_via_cli calls sts service."""
        mock_run.return_value = MagicMock(returncode=0, stdout="123456789012")
        get_aws_account_id_via_cli()
        call_args = mock_run.call_args[0][0]
        assert "sts" in call_args

    @patch("test_fixtures.integration.helpers.subprocess.run")
    def test_calls_get_caller_identity_action(self, mock_run):
        """get_aws_account_id_via_cli calls get-caller-identity action."""
        mock_run.return_value = MagicMock(returncode=0, stdout="123456789012")
        get_aws_account_id_via_cli()
        call_args = mock_run.call_args[0][0]
        assert "get-caller-identity" in call_args


class TestGetAWSAccountIdViaCLIFailure:
    """Tests for get_aws_account_id_via_cli on failure."""

    @patch("test_fixtures.integration.helpers.subprocess.run")
    def test_returns_empty_string_on_failure(self, mock_run):
        """get_aws_account_id_via_cli returns empty string on failure."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = get_aws_account_id_via_cli()
        assert result == ""


# === handle_ecr_authorization_error ===


class TestHandleECRAuthorizationErrorAccessDenied:
    """Tests for handle_ecr_authorization_error with AccessDenied."""

    def test_fails_on_access_denied(self):
        """handle_ecr_authorization_error fails on AccessDeniedException."""
        error = _create_client_error("AccessDeniedException")
        with pytest.raises(pytest.fail.Exception):
            handle_ecr_authorization_error(
                error, "ecr:DescribeRepositories", "my-repo"
            )

    def test_error_message_contains_operation(self):
        """handle_ecr_authorization_error error contains operation."""
        error = _create_client_error("AccessDeniedException")
        with pytest.raises(pytest.fail.Exception, match="ecr:DescribeRepositories"):
            handle_ecr_authorization_error(
                error, "ecr:DescribeRepositories", "my-repo"
            )

    def test_error_message_contains_repository_name(self):
        """handle_ecr_authorization_error error contains repository name."""
        error = _create_client_error("AccessDeniedException")
        with pytest.raises(pytest.fail.Exception, match="my-repo"):
            handle_ecr_authorization_error(
                error, "ecr:DescribeRepositories", "my-repo"
            )


class TestHandleECRAuthorizationErrorRepositoryNotFound:
    """Tests for handle_ecr_authorization_error with RepositoryNotFound."""

    def test_does_not_raise_on_repository_not_found(self):
        """handle_ecr_authorization_error does not raise on RepositoryNotFoundException."""
        error = _create_client_error("RepositoryNotFoundException")
        result = handle_ecr_authorization_error(error, "ecr:DescribeRepositories", "my-repo")
        assert result is None


class TestHandleECRAuthorizationErrorOtherErrors:
    """Tests for handle_ecr_authorization_error with other errors."""

    def test_reraises_other_errors(self):
        """handle_ecr_authorization_error reraises other errors."""
        error = _create_client_error("ServiceException")
        with pytest.raises(ClientError, match="ServiceException"):
            handle_ecr_authorization_error(error, "ecr:DescribeRepositories", "my-repo")


# === check_s3_head_bucket_permission ===


class TestCheckS3HeadBucketPermissionSuccess:
    """Tests for check_s3_head_bucket_permission on success."""

    def test_does_not_raise_when_bucket_accessible(self):
        """check_s3_head_bucket_permission does not raise when bucket accessible."""
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = {}
        result = check_s3_head_bucket_permission(mock_client, "my-bucket")
        assert result is None

    def test_calls_head_bucket_with_bucket_name(self):
        """check_s3_head_bucket_permission calls head_bucket with bucket name."""
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = {}
        check_s3_head_bucket_permission(mock_client, "my-bucket")
        assert mock_client.head_bucket.call_args[1]["Bucket"] == "my-bucket"


class TestCheckS3HeadBucketPermissionAccessDenied:
    """Tests for check_s3_head_bucket_permission with access denied."""

    def test_fails_on_403_error(self):
        """check_s3_head_bucket_permission fails on 403 error."""
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = _create_client_error("403")
        with pytest.raises(pytest.fail.Exception):
            check_s3_head_bucket_permission(mock_client, "my-bucket")

    def test_fails_on_access_denied_error(self):
        """check_s3_head_bucket_permission fails on AccessDenied error."""
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = _create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            check_s3_head_bucket_permission(mock_client, "my-bucket")

    def test_error_message_contains_bucket_name(self):
        """check_s3_head_bucket_permission error contains bucket name."""
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = _create_client_error("403")
        with pytest.raises(pytest.fail.Exception, match="my-bucket"):
            check_s3_head_bucket_permission(mock_client, "my-bucket")


class TestCheckS3HeadBucketPermissionBucketNotFound:
    """Tests for check_s3_head_bucket_permission with bucket not found."""

    def test_does_not_raise_on_404_error(self):
        """check_s3_head_bucket_permission does not raise on 404 error."""
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = _create_client_error("404")
        result = check_s3_head_bucket_permission(mock_client, "my-bucket")
        assert result is None


class TestCheckS3HeadBucketPermissionOtherErrors:
    """Tests for check_s3_head_bucket_permission with other errors."""

    def test_reraises_other_errors(self):
        """check_s3_head_bucket_permission reraises other errors."""
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = _create_client_error("ServiceException")
        with pytest.raises(ClientError, match="ServiceException"):
            check_s3_head_bucket_permission(mock_client, "my-bucket")


# === skip_if_api_gateway_unavailable ===


class TestSkipIfAPIGatewayUnavailableAvailable:
    """Tests for skip_if_api_gateway_unavailable when available."""

    def test_does_not_skip_when_api_exists(self):
        """skip_if_api_gateway_unavailable does not skip when API exists."""
        api_gateway_info = {"id": "abc123", "exists": True}
        result = skip_if_api_gateway_unavailable(api_gateway_info)
        assert result is None


class TestSkipIfAPIGatewayUnavailableNoId:
    """Tests for skip_if_api_gateway_unavailable when no ID."""

    def test_skips_when_id_is_none(self):
        """skip_if_api_gateway_unavailable skips when ID is None."""
        api_gateway_info = {"id": None, "exists": False}
        with pytest.raises(pytest.skip.Exception):
            skip_if_api_gateway_unavailable(api_gateway_info)


class TestSkipIfAPIGatewayUnavailableDoesNotExist:
    """Tests for skip_if_api_gateway_unavailable when does not exist."""

    def test_skips_when_api_does_not_exist(self):
        """skip_if_api_gateway_unavailable skips when API does not exist."""
        api_gateway_info = {"id": "abc123", "exists": False}
        with pytest.raises(pytest.skip.Exception):
            skip_if_api_gateway_unavailable(api_gateway_info)


# === check_state_file_readable ===


class TestCheckStateFileReadableSuccess:
    """Tests for check_state_file_readable on success."""

    def test_does_not_raise_when_file_readable(self):
        """check_state_file_readable does not raise when file readable."""
        mock_client = MagicMock()
        mock_client.head_object.return_value = {}
        result = check_state_file_readable(mock_client, "my-bucket", "state/terraform.tfstate")
        assert result is None

    def test_calls_head_object_with_bucket_and_key(self):
        """check_state_file_readable calls head_object with bucket and key."""
        mock_client = MagicMock()
        mock_client.head_object.return_value = {}
        check_state_file_readable(mock_client, "my-bucket", "state/terraform.tfstate")
        assert mock_client.head_object.call_args[1]["Bucket"] == "my-bucket"


class TestCheckStateFileReadableAccessDenied:
    """Tests for check_state_file_readable with access denied."""

    def test_fails_on_403_error(self):
        """check_state_file_readable fails on 403 error."""
        mock_client = MagicMock()
        mock_client.head_object.side_effect = _create_client_error("403")
        with pytest.raises(pytest.fail.Exception):
            check_state_file_readable(
                mock_client, "my-bucket", "state/terraform.tfstate"
            )

    def test_error_message_contains_state_key(self):
        """check_state_file_readable error contains state key."""
        mock_client = MagicMock()
        mock_client.head_object.side_effect = _create_client_error("403")
        with pytest.raises(pytest.fail.Exception, match="state/terraform.tfstate"):
            check_state_file_readable(
                mock_client, "my-bucket", "state/terraform.tfstate"
            )


class TestCheckStateFileReadableNotFound:
    """Tests for check_state_file_readable with file not found."""

    def test_skips_on_404_error(self):
        """check_state_file_readable skips on 404 error."""
        mock_client = MagicMock()
        mock_client.head_object.side_effect = _create_client_error("404")
        with pytest.raises(pytest.skip.Exception):
            check_state_file_readable(
                mock_client, "my-bucket", "state/terraform.tfstate"
            )


class TestCheckStateFileReadableOtherErrors:
    """Tests for check_state_file_readable with other errors."""

    def test_reraises_other_errors(self):
        """check_state_file_readable reraises other errors."""
        mock_client = MagicMock()
        mock_client.head_object.side_effect = _create_client_error("ServiceException")
        with pytest.raises(ClientError, match="ServiceException"):
            check_state_file_readable(
                mock_client, "my-bucket", "state/terraform.tfstate"
            )


# === assert_api_gateway_exists ===


class TestAssertAPIGatewayExistsSuccess:
    """Tests for assert_api_gateway_exists when API exists."""

    def test_does_not_raise_when_api_exists(self):
        """assert_api_gateway_exists does not raise when API exists."""
        api_gateway_info = {"id": "abc123", "exists": True}
        result = assert_api_gateway_exists(api_gateway_info)
        assert result is None


class TestAssertAPIGatewayExistsNoId:
    """Tests for assert_api_gateway_exists when no ID."""

    def test_skips_when_id_is_none(self):
        """assert_api_gateway_exists skips when ID is None."""
        api_gateway_info = {"id": None, "exists": False}
        with pytest.raises(pytest.skip.Exception):
            assert_api_gateway_exists(api_gateway_info)


class TestAssertAPIGatewayExistsDoesNotExist:
    """Tests for assert_api_gateway_exists when API does not exist."""

    def test_raises_assertion_when_api_does_not_exist(self):
        """assert_api_gateway_exists raises AssertionError when API does not exist."""
        api_gateway_info = {"id": "abc123", "exists": False}
        with pytest.raises(AssertionError):
            assert_api_gateway_exists(api_gateway_info)

    def test_error_message_contains_api_id(self):
        """assert_api_gateway_exists error contains API ID."""
        api_gateway_info = {"id": "abc123xyz", "exists": False}
        with pytest.raises(AssertionError, match="abc123xyz"):
            assert_api_gateway_exists(api_gateway_info)

    def test_error_message_contains_terraform_path(self):
        """assert_api_gateway_exists error contains terraform path."""
        api_gateway_info = {"id": "abc123", "exists": False}
        with pytest.raises(AssertionError, match="custom/terraform/path"):
            assert_api_gateway_exists(api_gateway_info, "custom/terraform/path")


# === assert_iam_role_name_is_pascalcase ===


class TestAssertIAMRoleNameIsPascalCaseValid:
    """Tests for assert_iam_role_name_is_pascalcase with valid name."""

    def test_does_not_raise_when_name_valid(self):
        """assert_iam_role_name_is_pascalcase does not raise when name valid."""
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyServiceRole"}}
        validate_func = MagicMock(return_value=None)
        result = assert_iam_role_name_is_pascalcase(mock_client, "MyServiceRole", validate_func)
        assert result is None

    def test_calls_get_role_with_role_name(self):
        """assert_iam_role_name_is_pascalcase calls get_role with role name."""
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyServiceRole"}}
        validate_func = MagicMock(return_value=None)
        assert_iam_role_name_is_pascalcase(mock_client, "MyServiceRole", validate_func)
        mock_client.get_role.assert_called_once_with(RoleName="MyServiceRole")

    def test_calls_validate_func_with_actual_name(self):
        """assert_iam_role_name_is_pascalcase calls validate function with actual name."""
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "ActualRoleName"}}
        validate_func = MagicMock(return_value=None)
        assert_iam_role_name_is_pascalcase(mock_client, "RoleToCheck", validate_func)
        validate_func.assert_called_once_with("ActualRoleName")


class TestAssertIAMRoleNameIsPascalCaseInvalid:
    """Tests for assert_iam_role_name_is_pascalcase with invalid name."""

    def test_raises_assertion_when_name_invalid(self):
        """assert_iam_role_name_is_pascalcase raises AssertionError when invalid."""
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "my_service_role"}}
        validate_func = MagicMock(return_value="not PascalCase")
        with pytest.raises(AssertionError):
            assert_iam_role_name_is_pascalcase(
                mock_client, "my_service_role", validate_func
            )

    def test_error_message_contains_actual_name(self):
        """assert_iam_role_name_is_pascalcase error contains actual name."""
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "bad_name"}}
        validate_func = MagicMock(return_value="not PascalCase")
        with pytest.raises(AssertionError, match="bad_name"):
            assert_iam_role_name_is_pascalcase(mock_client, "bad_name", validate_func)

    def test_error_message_contains_validation_error(self):
        """assert_iam_role_name_is_pascalcase error contains validation error."""
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "bad_name"}}
        validate_func = MagicMock(return_value="contains_underscore")
        with pytest.raises(AssertionError, match="contains_underscore"):
            assert_iam_role_name_is_pascalcase(mock_client, "bad_name", validate_func)


# === NO_CREDENTIALS_MESSAGE ===


class TestNoCredentialsMessage:
    """Tests for NO_CREDENTIALS_MESSAGE constant."""

    def test_message_contains_aws(self):
        """NO_CREDENTIALS_MESSAGE contains 'AWS'."""
        assert "AWS" in NO_CREDENTIALS_MESSAGE

    def test_message_contains_credentials(self):
        """NO_CREDENTIALS_MESSAGE contains 'credentials'."""
        assert "credentials" in NO_CREDENTIALS_MESSAGE
