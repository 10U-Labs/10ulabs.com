from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from boto_mocks import create_client_error
import test_fixtures.integration as integration_module


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
