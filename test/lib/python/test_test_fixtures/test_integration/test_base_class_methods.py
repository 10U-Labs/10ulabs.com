"""Unit tests that run the earlier layers' base class methods.

Each test builds a base class from test_fixtures.integration, hands
its method a mocked client and reads what the method does with it.
"""
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from boto_mocks import create_client_error
import test_fixtures.integration as integration_module


class TestLayer1AuthenticationTestsExecution:
    """Tests that execute Layer1AuthenticationTests methods."""

    def test_credentials_are_available_success(self):
        """Test test_aws_credentials_are_available with valid client."""
        instance = integration_module.Layer1AuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123"}
        assert instance.test_aws_credentials_are_available(mock_client) is None

    def test_credentials_are_valid_success(self):
        """Test test_aws_credentials_are_valid with valid client."""
        instance = integration_module.Layer1AuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123"}
        assert instance.test_aws_credentials_are_valid(mock_client) is None

    def test_credentials_return_account_success(self):
        """Test test_aws_credentials_return_account with Account in response."""
        instance = integration_module.Layer1AuthenticationTests()
        caller_identity = {"Account": "123456789012", "Arn": "arn:aws:..."}
        assert instance.test_aws_credentials_return_account(caller_identity) is None

    def test_credentials_return_account_fails_without_account(self):
        """Test test_aws_credentials_return_account fails without Account."""
        instance = integration_module.Layer1AuthenticationTests()
        caller_identity = {"Arn": "arn:aws:..."}
        with pytest.raises(AssertionError):
            instance.test_aws_credentials_return_account(caller_identity)

    def test_credentials_return_arn_success(self):
        """Test test_aws_credentials_return_arn with Arn in response."""
        instance = integration_module.Layer1AuthenticationTests()
        caller_identity = {"Account": "123", "Arn": "arn:aws:sts::123:assumed-role/r/s"}
        assert instance.test_aws_credentials_return_arn(caller_identity) is None

    def test_credentials_return_arn_fails_without_arn(self):
        """Test test_aws_credentials_return_arn fails without Arn."""
        instance = integration_module.Layer1AuthenticationTests()
        caller_identity = {"Account": "123"}
        with pytest.raises(AssertionError):
            instance.test_aws_credentials_return_arn(caller_identity)

    def test_caller_identity_is_role_with_assumed_role(self):
        """Test test_caller_identity_is_role with assumed-role ARN."""
        instance = integration_module.Layer1AuthenticationTests()
        caller_identity = {"Arn": "arn:aws:sts::123:assumed-role/MyRole/session"}
        assert instance.test_caller_identity_is_role(caller_identity) is None

    def test_caller_identity_is_role_with_role_arn(self):
        """Test test_caller_identity_is_role with role ARN."""
        instance = integration_module.Layer1AuthenticationTests()
        caller_identity = {"Arn": "arn:aws:iam::123:role/MyRole"}
        assert instance.test_caller_identity_is_role(caller_identity) is None

    def test_caller_identity_is_role_fails_with_user(self):
        """Test test_caller_identity_is_role fails with user ARN."""
        instance = integration_module.Layer1AuthenticationTests()
        caller_identity = {"Arn": "arn:aws:iam::123:user/MyUser"}
        with pytest.raises(AssertionError):
            instance.test_caller_identity_is_role(caller_identity)


class TestLayer2IAMAuthorizationTestsExecution:
    """Tests that execute Layer2IAMAuthorizationTests methods."""

    def test_can_call_iam_get_role_api_success(self):
        """Test test_can_call_iam_get_role_api with successful call."""
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {}}
        assert instance.test_can_call_iam_get_role_api(mock_client, "MyRole") is None

    def test_can_call_iam_get_role_api_skips_when_no_role_name(self):
        """Test test_can_call_iam_get_role_api skips when role name empty."""
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        with pytest.raises(pytest.skip.Exception):
            instance.test_can_call_iam_get_role_api(mock_client, "")

    def test_can_call_iam_get_role_api_fails_on_access_denied(self):
        """Test test_can_call_iam_get_role_api fails on AccessDenied."""
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_call_iam_get_role_api(mock_client, "MyRole")

    def test_can_call_iam_get_role_api_ok_on_no_such_entity(self):
        """Test test_can_call_iam_get_role_api passes on NoSuchEntity."""
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("NoSuchEntity")
        assert instance.test_can_call_iam_get_role_api(mock_client, "MyRole") is None

    def test_can_call_iam_get_role_api_reraises_other_errors(self):
        """Test test_can_call_iam_get_role_api re-raises other errors."""
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_call_iam_get_role_api(mock_client, "MyRole")

    def test_can_list_attached_policies_success(self):
        """Test test_can_list_attached_policies with successful call."""
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.return_value = {"AttachedPolicies": []}
        assert instance.test_can_list_attached_policies(mock_client, "MyRole") is None

    def test_can_list_attached_policies_skips_when_no_role_name(self):
        """Test test_can_list_attached_policies skips when role name empty."""
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        with pytest.raises(pytest.skip.Exception):
            instance.test_can_list_attached_policies(mock_client, "")

    def test_can_list_attached_policies_fails_on_access_denied(self):
        """Test test_can_list_attached_policies fails on AccessDenied."""
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.side_effect = create_client_error(
            "AccessDenied"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_attached_policies(mock_client, "MyRole")

    def test_can_list_attached_policies_ok_on_no_such_entity(self):
        """Test test_can_list_attached_policies passes on NoSuchEntity."""
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.side_effect = create_client_error(
            "NoSuchEntity"
        )
        assert instance.test_can_list_attached_policies(mock_client, "MyRole") is None

    def test_can_list_attached_policies_reraises_other_errors(self):
        """Test test_can_list_attached_policies re-raises other errors."""
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.side_effect = create_client_error(
            "InternalError"
        )
        with pytest.raises(ClientError):
            instance.test_can_list_attached_policies(mock_client, "MyRole")


class TestLayer2S3AuthorizationTestsExecution:
    """Tests that execute Layer2S3AuthorizationTests methods."""

    def test_can_call_s3_head_bucket_api_success(self):
        """Test test_can_call_s3_head_bucket_api with successful call."""
        instance = integration_module.Layer2S3AuthorizationTests()
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = {}
        assert instance.test_can_call_s3_head_bucket_api(mock_client, "my-bucket") is None

    def test_can_call_s3_head_bucket_api_fails_on_403(self):
        """Test test_can_call_s3_head_bucket_api fails on 403."""
        instance = integration_module.Layer2S3AuthorizationTests()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("403")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_call_s3_head_bucket_api(mock_client, "my-bucket")

    def test_can_call_s3_head_bucket_api_ok_on_404(self):
        """Test test_can_call_s3_head_bucket_api passes on 404."""
        instance = integration_module.Layer2S3AuthorizationTests()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("404")
        assert instance.test_can_call_s3_head_bucket_api(mock_client, "my-bucket") is None

    def test_can_call_s3_head_bucket_api_reraises_other_errors(self):
        """Test test_can_call_s3_head_bucket_api re-raises other errors."""
        instance = integration_module.Layer2S3AuthorizationTests()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("500")
        with pytest.raises(ClientError):
            instance.test_can_call_s3_head_bucket_api(mock_client, "my-bucket")

    def test_state_bucket_name_configured_success(self):
        """Test test_state_bucket_name_configured with valid name."""
        instance = integration_module.Layer2S3AuthorizationTests()
        assert instance.test_state_bucket_name_configured("my-state-bucket") is None

    def test_state_bucket_name_configured_fails_when_empty(self):
        """Test test_state_bucket_name_configured fails when empty."""
        instance = integration_module.Layer2S3AuthorizationTests()
        with pytest.raises(AssertionError):
            instance.test_state_bucket_name_configured("")


class TestLayer2ECRAuthorizationTestsExecution:
    """Tests that execute Layer2ECRAuthorizationTests methods."""

    def test_can_call_ecr_describe_repositories_api_success(self):
        """Test test_can_call_ecr_describe_repositories_api with successful call."""
        instance = integration_module.Layer2ECRAuthorizationTests()
        mock_client = MagicMock()
        mock_client.describe_repositories.return_value = {"repositories": []}
        assert instance.test_can_call_ecr_describe_repositories_api(mock_client) is None

    def test_can_call_ecr_describe_repositories_api_fails_on_access_denied(self):
        """Test test_can_call_ecr_describe_repositories_api fails on AccessDeniedException."""
        instance = integration_module.Layer2ECRAuthorizationTests()
        mock_client = MagicMock()
        mock_client.describe_repositories.side_effect = create_client_error(
            "AccessDeniedException"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_call_ecr_describe_repositories_api(mock_client)

    def test_can_call_ecr_describe_repositories_api_reraises_other_errors(self):
        """Test test_can_call_ecr_describe_repositories_api re-raises other errors."""
        instance = integration_module.Layer2ECRAuthorizationTests()
        mock_client = MagicMock()
        mock_client.describe_repositories.side_effect = create_client_error(
            "InternalError"
        )
        with pytest.raises(ClientError):
            instance.test_can_call_ecr_describe_repositories_api(mock_client)

    def test_ecr_client_is_valid_success(self):
        """Test test_ecr_client_is_valid with valid client."""
        instance = integration_module.Layer2ECRAuthorizationTests()
        mock_client = MagicMock()
        assert instance.test_ecr_client_is_valid(mock_client) is None

    def test_ecr_client_is_valid_fails_when_none(self):
        """Test test_ecr_client_is_valid fails when None."""
        instance = integration_module.Layer2ECRAuthorizationTests()
        with pytest.raises(AssertionError):
            instance.test_ecr_client_is_valid(None)


class TestLayer4TerraformStateExistenceTestsExecution:
    """Tests that execute Layer4TerraformStateExistenceTests methods."""

    def test_state_bucket_exists_success(self):
        """Test test_state_bucket_exists with existing bucket."""
        instance = integration_module.Layer4TerraformStateExistenceTests()
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = {}
        assert instance.test_state_bucket_exists(mock_client, "my-state-bucket") is None

    def test_state_bucket_exists_fails_on_404(self):
        """Test test_state_bucket_exists fails when bucket doesn't exist."""
        instance = integration_module.Layer4TerraformStateExistenceTests()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("404")
        with pytest.raises(pytest.fail.Exception):
            instance.test_state_bucket_exists(mock_client, "my-state-bucket")

    def test_state_bucket_exists_reraises_other_errors(self):
        """Test test_state_bucket_exists re-raises other errors."""
        instance = integration_module.Layer4TerraformStateExistenceTests()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("500")
        with pytest.raises(ClientError):
            instance.test_state_bucket_exists(mock_client, "my-state-bucket")

    def test_state_bucket_has_name_success(self):
        """Test test_state_bucket_has_name with valid name."""
        instance = integration_module.Layer4TerraformStateExistenceTests()
        assert instance.test_state_bucket_has_name("my-state-bucket") is None

    def test_state_bucket_has_name_fails_when_empty(self):
        """Test test_state_bucket_has_name fails when empty."""
        instance = integration_module.Layer4TerraformStateExistenceTests()
        with pytest.raises(AssertionError):
            instance.test_state_bucket_has_name("")


class TestLayer5S3ConfigurationTestsExecution:
    """Tests that execute Layer5S3ConfigurationTests methods."""

    def test_state_bucket_is_encrypted_success(self):
        """Test test_state_bucket_is_encrypted with encryption enabled."""
        instance = integration_module.Layer5S3ConfigurationTests()
        mock_client = MagicMock()
        mock_client.get_bucket_encryption.return_value = {
            "ServerSideEncryptionConfiguration": {
                "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
            }
        }
        assert instance.test_state_bucket_is_encrypted(mock_client, "my-bucket") is None

    def test_state_bucket_is_encrypted_fails_with_no_rules(self):
        """Test test_state_bucket_is_encrypted fails with no rules."""
        instance = integration_module.Layer5S3ConfigurationTests()
        mock_client = MagicMock()
        mock_client.get_bucket_encryption.return_value = {
            "ServerSideEncryptionConfiguration": {"Rules": []}
        }
        with pytest.raises(AssertionError):
            instance.test_state_bucket_is_encrypted(mock_client, "my-bucket")

    def test_state_bucket_is_encrypted_fails_on_not_found(self):
        """Test test_state_bucket_is_encrypted fails when no encryption configured."""
        instance = integration_module.Layer5S3ConfigurationTests()
        mock_client = MagicMock()
        mock_client.get_bucket_encryption.side_effect = create_client_error(
            "ServerSideEncryptionConfigurationNotFoundError"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_state_bucket_is_encrypted(mock_client, "my-bucket")

    def test_state_bucket_is_encrypted_reraises_other_errors(self):
        """Test test_state_bucket_is_encrypted re-raises other errors."""
        instance = integration_module.Layer5S3ConfigurationTests()
        mock_client = MagicMock()
        mock_client.get_bucket_encryption.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_state_bucket_is_encrypted(mock_client, "my-bucket")

    def test_state_bucket_versioning_disabled_when_disabled(self):
        """Test test_state_bucket_versioning_disabled passes when disabled."""
        instance = integration_module.Layer5S3ConfigurationTests()
        mock_client = MagicMock()
        mock_client.get_bucket_versioning.return_value = {"Status": "Suspended"}
        assert instance.test_state_bucket_versioning_disabled(mock_client, "my-bucket") is None

    def test_state_bucket_versioning_disabled_when_not_set(self):
        """Test test_state_bucket_versioning_disabled passes when not set."""
        instance = integration_module.Layer5S3ConfigurationTests()
        mock_client = MagicMock()
        mock_client.get_bucket_versioning.return_value = {}
        assert instance.test_state_bucket_versioning_disabled(mock_client, "my-bucket") is None

    def test_state_bucket_versioning_disabled_fails_when_enabled(self):
        """Test test_state_bucket_versioning_disabled fails when enabled."""
        instance = integration_module.Layer5S3ConfigurationTests()
        mock_client = MagicMock()
        mock_client.get_bucket_versioning.return_value = {"Status": "Enabled"}
        with pytest.raises(AssertionError):
            instance.test_state_bucket_versioning_disabled(mock_client, "my-bucket")


class TestLayer6S3CapabilityTestsExecution:
    """Tests that execute Layer6S3CapabilityTests methods."""

    def test_can_list_bucket_objects_success(self):
        """Test test_can_list_bucket_objects with successful call."""
        instance = integration_module.Layer6S3CapabilityTests()
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {"Contents": []}
        assert instance.test_can_list_bucket_objects(mock_client, "my-bucket") is None

    def test_can_list_bucket_objects_fails_on_error(self):
        """Test test_can_list_bucket_objects fails on ClientError."""
        instance = integration_module.Layer6S3CapabilityTests()
        mock_client = MagicMock()
        mock_client.list_objects_v2.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_bucket_objects(mock_client, "my-bucket")

    def test_can_get_bucket_location_success(self):
        """Test test_can_get_bucket_location with successful call."""
        instance = integration_module.Layer6S3CapabilityTests()
        mock_client = MagicMock()
        mock_client.get_bucket_location.return_value = {"LocationConstraint": "us-west-2"}
        assert instance.test_can_get_bucket_location(mock_client, "my-bucket") is None

    def test_can_get_bucket_location_fails_on_error(self):
        """Test test_can_get_bucket_location fails on ClientError."""
        instance = integration_module.Layer6S3CapabilityTests()
        mock_client = MagicMock()
        mock_client.get_bucket_location.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_get_bucket_location(mock_client, "my-bucket")


class TestLayer4IAMRoleExistenceTestsExecution:
    """Tests that execute Layer4IAMRoleExistenceTests methods."""

    def test_iam_role_exists_success(self):
        """Test test_iam_role_exists with existing role."""
        instance = integration_module.Layer4IAMRoleExistenceTests()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyRole"}}
        assert instance.test_iam_role_exists(mock_client, "MyRole") is None

    def test_iam_role_exists_skips_when_no_role_name(self):
        """Test test_iam_role_exists skips when role name empty."""
        instance = integration_module.Layer4IAMRoleExistenceTests()
        mock_client = MagicMock()
        with pytest.raises(pytest.skip.Exception):
            instance.test_iam_role_exists(mock_client, "")

    def test_iam_role_exists_fails_on_no_such_entity(self):
        """Test test_iam_role_exists fails when role doesn't exist."""
        instance = integration_module.Layer4IAMRoleExistenceTests()
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("NoSuchEntity")
        with pytest.raises(pytest.fail.Exception):
            instance.test_iam_role_exists(mock_client, "MyRole")

    def test_iam_role_exists_reraises_other_errors(self):
        """Test test_iam_role_exists re-raises other errors."""
        instance = integration_module.Layer4IAMRoleExistenceTests()
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_iam_role_exists(mock_client, "MyRole")

    def test_current_role_name_is_configured_success(self):
        """Test test_current_role_name_is_configured with valid name."""
        instance = integration_module.Layer4IAMRoleExistenceTests()
        assert instance.test_current_role_name_is_configured("MyRole") is None

    def test_current_role_name_is_configured_fails_when_empty(self):
        """Test test_current_role_name_is_configured fails when empty."""
        instance = integration_module.Layer4IAMRoleExistenceTests()
        with pytest.raises(AssertionError):
            instance.test_current_role_name_is_configured("")


class TestLayer5IAMConfigurationTestsExecution:
    """Tests that execute Layer5IAMConfigurationTests methods."""

    def test_role_has_administrator_access_policy_success(self):
        """Test test_role_has_administrator_access_policy with policy attached."""
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.return_value = {
            "AttachedPolicies": [{"PolicyName": "AdministratorAccess", "PolicyArn": "arn:..."}]
        }
        assert instance.test_role_has_administrator_access_policy(mock_client, "MyRole") is None

    def test_role_has_administrator_access_policy_skips_when_no_role(self):
        """Test test_role_has_administrator_access_policy skips when no role."""
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        with pytest.raises(pytest.skip.Exception):
            instance.test_role_has_administrator_access_policy(mock_client, "")

    def test_role_has_administrator_access_policy_fails_without_policy(self):
        """Test test_role_has_administrator_access_policy fails without policy."""
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.return_value = {
            "AttachedPolicies": [{"PolicyName": "ReadOnlyAccess", "PolicyArn": "arn:..."}]
        }
        with pytest.raises(AssertionError):
            instance.test_role_has_administrator_access_policy(mock_client, "MyRole")

    def test_role_has_administrator_access_policy_skips_on_access_denied(self):
        """Test test_role_has_administrator_access_policy skips on AccessDenied."""
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.skip.Exception):
            instance.test_role_has_administrator_access_policy(mock_client, "MyRole")

    def test_role_has_administrator_access_policy_reraises_other_errors(self):
        """Test test_role_has_administrator_access_policy re-raises other errors."""
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_role_has_administrator_access_policy(mock_client, "MyRole")

    def test_role_has_at_least_one_policy_success(self):
        """Test test_role_has_at_least_one_policy with policies attached."""
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.return_value = {
            "AttachedPolicies": [{"PolicyName": "SomePolicy", "PolicyArn": "arn:..."}]
        }
        assert instance.test_role_has_at_least_one_policy(mock_client, "MyRole") is None

    def test_role_has_at_least_one_policy_skips_when_no_role(self):
        """Test test_role_has_at_least_one_policy skips when no role."""
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        with pytest.raises(pytest.skip.Exception):
            instance.test_role_has_at_least_one_policy(mock_client, "")

    def test_role_has_at_least_one_policy_fails_without_policies(self):
        """Test test_role_has_at_least_one_policy fails without policies."""
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.return_value = {"AttachedPolicies": []}
        with pytest.raises(AssertionError):
            instance.test_role_has_at_least_one_policy(mock_client, "MyRole")

    def test_role_has_at_least_one_policy_skips_on_access_denied(self):
        """Test test_role_has_at_least_one_policy skips on AccessDenied."""
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.skip.Exception):
            instance.test_role_has_at_least_one_policy(mock_client, "MyRole")

    def test_role_has_at_least_one_policy_reraises_other_errors(self):
        """Test test_role_has_at_least_one_policy re-raises other errors."""
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_role_has_at_least_one_policy(mock_client, "MyRole")
