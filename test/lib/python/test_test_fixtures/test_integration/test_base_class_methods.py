from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from boto_mocks import create_client_error
import test_fixtures.integration as integration_module


class TestLayer1AuthenticationTestsExecution:
    def test_credentials_are_available_success(self):
        instance = integration_module.Layer1AuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123"}
        assert instance.test_aws_credentials_are_available(mock_client) is None

    def test_credentials_are_valid_success(self):
        instance = integration_module.Layer1AuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123"}
        assert instance.test_aws_credentials_are_valid(mock_client) is None

    def test_credentials_return_account_success(self):
        instance = integration_module.Layer1AuthenticationTests()
        caller_identity = {"Account": "123456789012", "Arn": "arn:aws:..."}
        assert instance.test_aws_credentials_return_account(caller_identity) is None

    def test_credentials_return_account_fails_without_account(self):
        instance = integration_module.Layer1AuthenticationTests()
        caller_identity = {"Arn": "arn:aws:..."}
        with pytest.raises(AssertionError):
            instance.test_aws_credentials_return_account(caller_identity)

    def test_credentials_return_arn_success(self):
        instance = integration_module.Layer1AuthenticationTests()
        caller_identity = {"Account": "123", "Arn": "arn:aws:sts::123:assumed-role/r/s"}
        assert instance.test_aws_credentials_return_arn(caller_identity) is None

    def test_credentials_return_arn_fails_without_arn(self):
        instance = integration_module.Layer1AuthenticationTests()
        caller_identity = {"Account": "123"}
        with pytest.raises(AssertionError):
            instance.test_aws_credentials_return_arn(caller_identity)

    def test_caller_identity_is_role_with_assumed_role(self):
        instance = integration_module.Layer1AuthenticationTests()
        caller_identity = {"Arn": "arn:aws:sts::123:assumed-role/MyRole/session"}
        assert instance.test_caller_identity_is_role(caller_identity) is None

    def test_caller_identity_is_role_with_role_arn(self):
        instance = integration_module.Layer1AuthenticationTests()
        caller_identity = {"Arn": "arn:aws:iam::123:role/MyRole"}
        assert instance.test_caller_identity_is_role(caller_identity) is None

    def test_caller_identity_is_role_fails_with_user(self):
        instance = integration_module.Layer1AuthenticationTests()
        caller_identity = {"Arn": "arn:aws:iam::123:user/MyUser"}
        with pytest.raises(AssertionError):
            instance.test_caller_identity_is_role(caller_identity)


class TestLayer2IAMAuthorizationTestsExecution:
    def test_can_call_iam_get_role_api_success(self):
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {}}
        assert instance.test_can_call_iam_get_role_api(mock_client, "MyRole") is None

    def test_can_call_iam_get_role_api_skips_when_no_role_name(self):
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        with pytest.raises(pytest.skip.Exception):
            instance.test_can_call_iam_get_role_api(mock_client, "")

    def test_can_call_iam_get_role_api_fails_on_access_denied(self):
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_call_iam_get_role_api(mock_client, "MyRole")

    def test_can_call_iam_get_role_api_ok_on_no_such_entity(self):
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("NoSuchEntity")
        assert instance.test_can_call_iam_get_role_api(mock_client, "MyRole") is None

    def test_can_call_iam_get_role_api_reraises_other_errors(self):
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_call_iam_get_role_api(mock_client, "MyRole")

    def test_can_list_attached_policies_success(self):
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.return_value = {"AttachedPolicies": []}
        assert instance.test_can_list_attached_policies(mock_client, "MyRole") is None

    def test_can_list_attached_policies_skips_when_no_role_name(self):
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        with pytest.raises(pytest.skip.Exception):
            instance.test_can_list_attached_policies(mock_client, "")

    def test_can_list_attached_policies_fails_on_access_denied(self):
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.side_effect = create_client_error(
            "AccessDenied"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_attached_policies(mock_client, "MyRole")

    def test_can_list_attached_policies_ok_on_no_such_entity(self):
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.side_effect = create_client_error(
            "NoSuchEntity"
        )
        assert instance.test_can_list_attached_policies(mock_client, "MyRole") is None

    def test_can_list_attached_policies_reraises_other_errors(self):
        instance = integration_module.Layer2IAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.side_effect = create_client_error(
            "InternalError"
        )
        with pytest.raises(ClientError):
            instance.test_can_list_attached_policies(mock_client, "MyRole")


class TestLayer2S3AuthorizationTestsExecution:
    def test_can_call_s3_head_bucket_api_success(self):
        instance = integration_module.Layer2S3AuthorizationTests()
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = {}
        assert instance.test_can_call_s3_head_bucket_api(mock_client, "my-bucket") is None

    def test_can_call_s3_head_bucket_api_fails_on_403(self):
        instance = integration_module.Layer2S3AuthorizationTests()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("403")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_call_s3_head_bucket_api(mock_client, "my-bucket")

    def test_can_call_s3_head_bucket_api_ok_on_404(self):
        instance = integration_module.Layer2S3AuthorizationTests()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("404")
        assert instance.test_can_call_s3_head_bucket_api(mock_client, "my-bucket") is None

    def test_can_call_s3_head_bucket_api_reraises_other_errors(self):
        instance = integration_module.Layer2S3AuthorizationTests()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("500")
        with pytest.raises(ClientError):
            instance.test_can_call_s3_head_bucket_api(mock_client, "my-bucket")

    def test_state_bucket_name_configured_success(self):
        instance = integration_module.Layer2S3AuthorizationTests()
        assert instance.test_state_bucket_name_configured("my-state-bucket") is None

    def test_state_bucket_name_configured_fails_when_empty(self):
        instance = integration_module.Layer2S3AuthorizationTests()
        with pytest.raises(AssertionError):
            instance.test_state_bucket_name_configured("")


class TestLayer2ECRAuthorizationTestsExecution:
    def test_can_call_ecr_describe_repositories_api_success(self):
        instance = integration_module.Layer2ECRAuthorizationTests()
        mock_client = MagicMock()
        mock_client.describe_repositories.return_value = {"repositories": []}
        assert instance.test_can_call_ecr_describe_repositories_api(mock_client) is None

    def test_can_call_ecr_describe_repositories_api_fails_on_access_denied(self):
        instance = integration_module.Layer2ECRAuthorizationTests()
        mock_client = MagicMock()
        mock_client.describe_repositories.side_effect = create_client_error(
            "AccessDeniedException"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_call_ecr_describe_repositories_api(mock_client)

    def test_can_call_ecr_describe_repositories_api_reraises_other_errors(self):
        instance = integration_module.Layer2ECRAuthorizationTests()
        mock_client = MagicMock()
        mock_client.describe_repositories.side_effect = create_client_error(
            "InternalError"
        )
        with pytest.raises(ClientError):
            instance.test_can_call_ecr_describe_repositories_api(mock_client)

    def test_ecr_client_is_valid_success(self):
        instance = integration_module.Layer2ECRAuthorizationTests()
        mock_client = MagicMock()
        assert instance.test_ecr_client_is_valid(mock_client) is None

    def test_ecr_client_is_valid_fails_when_none(self):
        instance = integration_module.Layer2ECRAuthorizationTests()
        with pytest.raises(AssertionError):
            instance.test_ecr_client_is_valid(None)


class TestLayer4TerraformStateExistenceTestsExecution:
    def test_state_bucket_exists_success(self):
        instance = integration_module.Layer4TerraformStateExistenceTests()
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = {}
        assert instance.test_state_bucket_exists(mock_client, "my-state-bucket") is None

    def test_state_bucket_exists_fails_on_404(self):
        instance = integration_module.Layer4TerraformStateExistenceTests()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("404")
        with pytest.raises(pytest.fail.Exception):
            instance.test_state_bucket_exists(mock_client, "my-state-bucket")

    def test_state_bucket_exists_reraises_other_errors(self):
        instance = integration_module.Layer4TerraformStateExistenceTests()
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = create_client_error("500")
        with pytest.raises(ClientError):
            instance.test_state_bucket_exists(mock_client, "my-state-bucket")

    def test_state_bucket_has_name_success(self):
        instance = integration_module.Layer4TerraformStateExistenceTests()
        assert instance.test_state_bucket_has_name("my-state-bucket") is None

    def test_state_bucket_has_name_fails_when_empty(self):
        instance = integration_module.Layer4TerraformStateExistenceTests()
        with pytest.raises(AssertionError):
            instance.test_state_bucket_has_name("")


class TestLayer5S3ConfigurationTestsExecution:
    def test_state_bucket_is_encrypted_success(self):
        instance = integration_module.Layer5S3ConfigurationTests()
        mock_client = MagicMock()
        mock_client.get_bucket_encryption.return_value = {
            "ServerSideEncryptionConfiguration": {
                "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
            }
        }
        assert instance.test_state_bucket_is_encrypted(mock_client, "my-bucket") is None

    def test_state_bucket_is_encrypted_fails_with_no_rules(self):
        instance = integration_module.Layer5S3ConfigurationTests()
        mock_client = MagicMock()
        mock_client.get_bucket_encryption.return_value = {
            "ServerSideEncryptionConfiguration": {"Rules": []}
        }
        with pytest.raises(AssertionError):
            instance.test_state_bucket_is_encrypted(mock_client, "my-bucket")

    def test_state_bucket_is_encrypted_fails_on_not_found(self):
        instance = integration_module.Layer5S3ConfigurationTests()
        mock_client = MagicMock()
        mock_client.get_bucket_encryption.side_effect = create_client_error(
            "ServerSideEncryptionConfigurationNotFoundError"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_state_bucket_is_encrypted(mock_client, "my-bucket")

    def test_state_bucket_is_encrypted_reraises_other_errors(self):
        instance = integration_module.Layer5S3ConfigurationTests()
        mock_client = MagicMock()
        mock_client.get_bucket_encryption.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_state_bucket_is_encrypted(mock_client, "my-bucket")

    def test_state_bucket_versioning_disabled_when_disabled(self):
        instance = integration_module.Layer5S3ConfigurationTests()
        mock_client = MagicMock()
        mock_client.get_bucket_versioning.return_value = {"Status": "Suspended"}
        assert instance.test_state_bucket_versioning_disabled(mock_client, "my-bucket") is None

    def test_state_bucket_versioning_disabled_when_not_set(self):
        instance = integration_module.Layer5S3ConfigurationTests()
        mock_client = MagicMock()
        mock_client.get_bucket_versioning.return_value = {}
        assert instance.test_state_bucket_versioning_disabled(mock_client, "my-bucket") is None

    def test_state_bucket_versioning_disabled_fails_when_enabled(self):
        instance = integration_module.Layer5S3ConfigurationTests()
        mock_client = MagicMock()
        mock_client.get_bucket_versioning.return_value = {"Status": "Enabled"}
        with pytest.raises(AssertionError):
            instance.test_state_bucket_versioning_disabled(mock_client, "my-bucket")


class TestLayer6S3CapabilityTestsExecution:
    def test_can_list_bucket_objects_success(self):
        instance = integration_module.Layer6S3CapabilityTests()
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {"Contents": []}
        assert instance.test_can_list_bucket_objects(mock_client, "my-bucket") is None

    def test_can_list_bucket_objects_fails_on_error(self):
        instance = integration_module.Layer6S3CapabilityTests()
        mock_client = MagicMock()
        mock_client.list_objects_v2.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_bucket_objects(mock_client, "my-bucket")

    def test_can_get_bucket_location_success(self):
        instance = integration_module.Layer6S3CapabilityTests()
        mock_client = MagicMock()
        mock_client.get_bucket_location.return_value = {"LocationConstraint": "us-west-2"}
        assert instance.test_can_get_bucket_location(mock_client, "my-bucket") is None

    def test_can_get_bucket_location_fails_on_error(self):
        instance = integration_module.Layer6S3CapabilityTests()
        mock_client = MagicMock()
        mock_client.get_bucket_location.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_get_bucket_location(mock_client, "my-bucket")


class TestLayer4IAMRoleExistenceTestsExecution:
    def test_iam_role_exists_success(self):
        instance = integration_module.Layer4IAMRoleExistenceTests()
        mock_client = MagicMock()
        mock_client.get_role.return_value = {"Role": {"RoleName": "MyRole"}}
        assert instance.test_iam_role_exists(mock_client, "MyRole") is None

    def test_iam_role_exists_skips_when_no_role_name(self):
        instance = integration_module.Layer4IAMRoleExistenceTests()
        mock_client = MagicMock()
        with pytest.raises(pytest.skip.Exception):
            instance.test_iam_role_exists(mock_client, "")

    def test_iam_role_exists_fails_on_no_such_entity(self):
        instance = integration_module.Layer4IAMRoleExistenceTests()
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("NoSuchEntity")
        with pytest.raises(pytest.fail.Exception):
            instance.test_iam_role_exists(mock_client, "MyRole")

    def test_iam_role_exists_reraises_other_errors(self):
        instance = integration_module.Layer4IAMRoleExistenceTests()
        mock_client = MagicMock()
        mock_client.get_role.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_iam_role_exists(mock_client, "MyRole")

    def test_current_role_name_is_configured_success(self):
        instance = integration_module.Layer4IAMRoleExistenceTests()
        assert instance.test_current_role_name_is_configured("MyRole") is None

    def test_current_role_name_is_configured_fails_when_empty(self):
        instance = integration_module.Layer4IAMRoleExistenceTests()
        with pytest.raises(AssertionError):
            instance.test_current_role_name_is_configured("")


class TestLayer5IAMConfigurationTestsExecution:
    def test_role_has_administrator_access_policy_success(self):
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.return_value = {
            "AttachedPolicies": [{"PolicyName": "AdministratorAccess", "PolicyArn": "arn:..."}]
        }
        assert instance.test_role_has_administrator_access_policy(mock_client, "MyRole") is None

    def test_role_has_administrator_access_policy_skips_when_no_role(self):
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        with pytest.raises(pytest.skip.Exception):
            instance.test_role_has_administrator_access_policy(mock_client, "")

    def test_role_has_administrator_access_policy_fails_without_policy(self):
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.return_value = {
            "AttachedPolicies": [{"PolicyName": "ReadOnlyAccess", "PolicyArn": "arn:..."}]
        }
        with pytest.raises(AssertionError):
            instance.test_role_has_administrator_access_policy(mock_client, "MyRole")

    def test_role_has_administrator_access_policy_skips_on_access_denied(self):
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.skip.Exception):
            instance.test_role_has_administrator_access_policy(mock_client, "MyRole")

    def test_role_has_administrator_access_policy_reraises_other_errors(self):
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_role_has_administrator_access_policy(mock_client, "MyRole")

    def test_role_has_at_least_one_policy_success(self):
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.return_value = {
            "AttachedPolicies": [{"PolicyName": "SomePolicy", "PolicyArn": "arn:..."}]
        }
        assert instance.test_role_has_at_least_one_policy(mock_client, "MyRole") is None

    def test_role_has_at_least_one_policy_skips_when_no_role(self):
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        with pytest.raises(pytest.skip.Exception):
            instance.test_role_has_at_least_one_policy(mock_client, "")

    def test_role_has_at_least_one_policy_fails_without_policies(self):
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.return_value = {"AttachedPolicies": []}
        with pytest.raises(AssertionError):
            instance.test_role_has_at_least_one_policy(mock_client, "MyRole")

    def test_role_has_at_least_one_policy_skips_on_access_denied(self):
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.skip.Exception):
            instance.test_role_has_at_least_one_policy(mock_client, "MyRole")

    def test_role_has_at_least_one_policy_reraises_other_errors(self):
        instance = integration_module.Layer5IAMConfigurationTests()
        mock_client = MagicMock()
        mock_client.list_attached_role_policies.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_role_has_at_least_one_policy(mock_client, "MyRole")
