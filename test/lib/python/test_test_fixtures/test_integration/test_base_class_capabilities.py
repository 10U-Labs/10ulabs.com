from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from boto_mocks import create_client_error
import test_fixtures.integration as integration_module


class TestLayer6IAMCapabilityTestsExecution:
    def test_can_list_buckets_success(self) -> None:
        instance = integration_module.Layer6IAMCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_buckets.return_value = {"Buckets": []}
        assert instance.test_can_list_buckets(mock_client) is None

    def test_can_list_buckets_fails_on_access_denied(self) -> None:
        instance = integration_module.Layer6IAMCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_buckets.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_buckets(mock_client)

    def test_can_list_buckets_reraises_other_errors(self) -> None:
        instance = integration_module.Layer6IAMCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_buckets.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_list_buckets(mock_client)

    def test_can_list_roles_success(self) -> None:
        instance = integration_module.Layer6IAMCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_roles.return_value = {"Roles": []}
        assert instance.test_can_list_roles(mock_client) is None

    def test_can_list_roles_fails_on_access_denied(self) -> None:
        instance = integration_module.Layer6IAMCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_roles.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_roles(mock_client)

    def test_can_list_roles_reraises_other_errors(self) -> None:
        instance = integration_module.Layer6IAMCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_roles.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_list_roles(mock_client)


class TestLayer6S3WriteCapabilityTestsExecution:
    def test_can_write_to_bucket_success(self) -> None:
        instance = integration_module.Layer6S3WriteCapabilityTests()
        mock_client = MagicMock()
        mock_client.put_object.return_value = {}
        mock_client.delete_object.return_value = {}
        assert instance.test_can_write_to_bucket(mock_client, "my-bucket") is None
        mock_client.put_object.assert_called_once()
        mock_client.delete_object.assert_called_once()

    def test_can_write_to_bucket_fails_on_access_denied(self) -> None:
        instance = integration_module.Layer6S3WriteCapabilityTests()
        mock_client = MagicMock()
        mock_client.put_object.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_write_to_bucket(mock_client, "my-bucket")

    def test_can_write_to_bucket_reraises_other_errors(self) -> None:
        instance = integration_module.Layer6S3WriteCapabilityTests()
        mock_client = MagicMock()
        mock_client.put_object.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_write_to_bucket(mock_client, "my-bucket")

    def test_can_write_to_bucket_cleanup_on_delete_failure(self) -> None:
        instance = integration_module.Layer6S3WriteCapabilityTests()
        mock_client = MagicMock()
        mock_client.put_object.return_value = {}
        mock_client.delete_object.side_effect = create_client_error("InternalError")
        assert instance.test_can_write_to_bucket(mock_client, "my-bucket") is None

    def test_can_delete_from_bucket_success(self) -> None:
        instance = integration_module.Layer6S3WriteCapabilityTests()
        mock_client = MagicMock()
        mock_client.put_object.return_value = {}
        mock_client.delete_object.return_value = {}
        assert instance.test_can_delete_from_bucket(mock_client, "my-bucket") is None

    def test_can_delete_from_bucket_fails_on_access_denied(self) -> None:
        instance = integration_module.Layer6S3WriteCapabilityTests()
        mock_client = MagicMock()
        mock_client.put_object.return_value = {}
        mock_client.delete_object.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_delete_from_bucket(mock_client, "my-bucket")

    def test_can_delete_from_bucket_reraises_other_errors(self) -> None:
        instance = integration_module.Layer6S3WriteCapabilityTests()
        mock_client = MagicMock()
        mock_client.put_object.return_value = {}
        mock_client.delete_object.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_delete_from_bucket(mock_client, "my-bucket")


class TestLayer1EndpointAuthenticationTestsExecution:
    def test_aws_credentials_are_valid_success(self) -> None:
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
        assert instance.test_aws_credentials_are_valid(mock_client) is None

    def test_aws_credentials_are_valid_fails_with_none_account(self) -> None:
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": None}
        with pytest.raises(AssertionError):
            instance.test_aws_credentials_are_valid(mock_client)

    def test_aws_credentials_return_account_id_success(self) -> None:
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
        assert instance.test_aws_credentials_return_account_id(mock_client) is None

    def test_aws_credentials_return_account_id_fails_with_wrong_length(self) -> None:
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "12345"}
        with pytest.raises(AssertionError):
            instance.test_aws_credentials_return_account_id(mock_client)

    def test_aws_credentials_return_arn_success(self) -> None:
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {
            "Account": "123",
            "Arn": "arn:aws:iam::123:role/MyRole"
        }
        assert instance.test_aws_credentials_return_arn(mock_client) is None

    def test_aws_credentials_return_arn_fails_without_arn(self) -> None:
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Account": "123"}
        with pytest.raises(AssertionError):
            instance.test_aws_credentials_return_arn(mock_client)

    def test_aws_credentials_arn_has_valid_format_success(self) -> None:
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {
            "Arn": "arn:aws:iam::123:role/MyRole"
        }
        assert instance.test_aws_credentials_arn_has_valid_format(mock_client) is None

    def test_aws_credentials_arn_has_valid_format_fails_with_invalid_arn(self) -> None:
        instance = integration_module.Layer1EndpointAuthenticationTests()
        mock_client = MagicMock()
        mock_client.get_caller_identity.return_value = {"Arn": "invalid-arn"}
        with pytest.raises(AssertionError):
            instance.test_aws_credentials_arn_has_valid_format(mock_client)


class TestLayer2APIGatewayAuthorizationTestsExecution:
    def test_can_describe_rest_apis_success(self) -> None:
        instance = integration_module.Layer2APIGatewayAuthorizationTests()
        mock_client = MagicMock()
        mock_client.get_rest_apis.return_value = {"items": []}
        assert instance.test_can_describe_rest_apis(mock_client) is None

    def test_can_describe_rest_apis_fails_on_access_denied(self) -> None:
        instance = integration_module.Layer2APIGatewayAuthorizationTests()
        mock_client = MagicMock()
        mock_client.get_rest_apis.side_effect = create_client_error(
            "AccessDeniedException"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_describe_rest_apis(mock_client)

    def test_can_describe_rest_apis_reraises_other_errors(self) -> None:
        instance = integration_module.Layer2APIGatewayAuthorizationTests()
        mock_client = MagicMock()
        mock_client.get_rest_apis.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_describe_rest_apis(mock_client)

    def test_can_access_specific_rest_api_success(self) -> None:
        instance = integration_module.Layer2APIGatewayAuthorizationTests()
        api_gateway_info = {"id": "abc123", "accessible": True}
        assert instance.test_can_access_specific_rest_api(api_gateway_info) is None

    def test_can_access_specific_rest_api_skips_when_id_is_none(self) -> None:
        instance = integration_module.Layer2APIGatewayAuthorizationTests()
        api_gateway_info = {"id": None, "accessible": False}
        with pytest.raises(pytest.skip.Exception):
            instance.test_can_access_specific_rest_api(api_gateway_info)

    def test_can_access_specific_rest_api_fails_when_not_accessible(self) -> None:
        instance = integration_module.Layer2APIGatewayAuthorizationTests()
        api_gateway_info = {"id": "abc123", "accessible": False}
        with pytest.raises(AssertionError):
            instance.test_can_access_specific_rest_api(api_gateway_info)


class TestLayer2LambdaAndIAMAuthorizationTestsExecution:
    def test_can_list_functions_success(self) -> None:
        instance = integration_module.Layer2LambdaAndIAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_functions.return_value = {"Functions": []}
        assert instance.test_can_list_functions(mock_client) is None

    def test_can_list_functions_fails_on_access_denied(self) -> None:
        instance = integration_module.Layer2LambdaAndIAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_functions.side_effect = create_client_error(
            "AccessDeniedException"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_functions(mock_client)

    def test_can_list_functions_reraises_other_errors(self) -> None:
        instance = integration_module.Layer2LambdaAndIAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_functions.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_list_functions(mock_client)

    def test_can_list_roles_iam_success(self) -> None:
        instance = integration_module.Layer2LambdaAndIAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_roles.return_value = {"Roles": []}
        assert instance.test_can_list_roles(mock_client) is None

    def test_can_list_roles_iam_fails_on_access_denied(self) -> None:
        instance = integration_module.Layer2LambdaAndIAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_roles.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_list_roles(mock_client)

    def test_can_list_roles_iam_reraises_other_errors(self) -> None:
        instance = integration_module.Layer2LambdaAndIAMAuthorizationTests()
        mock_client = MagicMock()
        mock_client.list_roles.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_list_roles(mock_client)


class TestLayer4APIBackendPrerequisiteTestsExecution:
    def test_api_gateway_id_output_exists_success(self) -> None:
        instance = integration_module.Layer4APIBackendPrerequisiteTests()
        outputs = {"api_gateway_id": "abc123xyz"}
        assert instance.test_api_gateway_id_output_exists(outputs) is None

    def test_api_gateway_id_output_exists_fails_when_missing(self) -> None:
        instance = integration_module.Layer4APIBackendPrerequisiteTests()
        outputs: Dict[str, str] = {}
        with pytest.raises(AssertionError):
            instance.test_api_gateway_id_output_exists(outputs)

    def test_api_gateway_id_output_exists_fails_when_empty(self) -> None:
        instance = integration_module.Layer4APIBackendPrerequisiteTests()
        outputs = {"api_gateway_id": ""}
        with pytest.raises(AssertionError):
            instance.test_api_gateway_id_output_exists(outputs)

    def test_api_gateway_exists_in_aws_success(self) -> None:
        instance = integration_module.Layer4APIBackendPrerequisiteTests()
        mock_client = MagicMock()
        mock_client.get_rest_api.return_value = {"id": "abc123"}
        outputs = {"api_gateway_id": "abc123"}
        assert instance.test_api_gateway_exists_in_aws(mock_client, outputs) is None

    def test_api_gateway_exists_in_aws_skips_when_no_id(self) -> None:
        instance = integration_module.Layer4APIBackendPrerequisiteTests()
        mock_client = MagicMock()
        outputs: Dict[str, str] = {}
        with pytest.raises(pytest.skip.Exception):
            instance.test_api_gateway_exists_in_aws(mock_client, outputs)

    def test_api_gateway_exists_in_aws_fails_on_not_found(self) -> None:
        instance = integration_module.Layer4APIBackendPrerequisiteTests()
        mock_client = MagicMock()
        mock_client.get_rest_api.side_effect = create_client_error("NotFoundException")
        outputs = {"api_gateway_id": "abc123"}
        with pytest.raises(pytest.fail.Exception):
            instance.test_api_gateway_exists_in_aws(mock_client, outputs)

    def test_api_gateway_exists_in_aws_reraises_other_errors(self) -> None:
        instance = integration_module.Layer4APIBackendPrerequisiteTests()
        mock_client = MagicMock()
        mock_client.get_rest_api.side_effect = create_client_error("InternalError")
        outputs = {"api_gateway_id": "abc123"}
        with pytest.raises(ClientError):
            instance.test_api_gateway_exists_in_aws(mock_client, outputs)


class TestLayer5APIGatewayRegionalTestsExecution:
    def test_api_gateway_is_regional_success(self) -> None:
        instance = integration_module.Layer5APIGatewayRegionalTests()
        api_gateway_info = {
            "id": "abc123",
            "exists": True,
            "endpoint_types": ["REGIONAL"]
        }
        assert instance.test_api_gateway_is_regional(api_gateway_info) is None

    def test_api_gateway_is_regional_skips_when_id_none(self) -> None:
        instance = integration_module.Layer5APIGatewayRegionalTests()
        api_gateway_info = {"id": None, "exists": False, "endpoint_types": []}
        with pytest.raises(pytest.skip.Exception):
            instance.test_api_gateway_is_regional(api_gateway_info)

    def test_api_gateway_is_regional_skips_when_not_exists(self) -> None:
        instance = integration_module.Layer5APIGatewayRegionalTests()
        api_gateway_info = {"id": "abc123", "exists": False, "endpoint_types": []}
        with pytest.raises(pytest.skip.Exception):
            instance.test_api_gateway_is_regional(api_gateway_info)

    def test_api_gateway_is_regional_fails_when_not_regional(self) -> None:
        instance = integration_module.Layer5APIGatewayRegionalTests()
        api_gateway_info = {
            "id": "abc123",
            "exists": True,
            "endpoint_types": ["EDGE"]
        }
        with pytest.raises(AssertionError):
            instance.test_api_gateway_is_regional(api_gateway_info)

    def test_api_gateway_info_has_id_success(self) -> None:
        instance = integration_module.Layer5APIGatewayRegionalTests()
        api_gateway_info = {"id": "abc123"}
        assert instance.test_api_gateway_info_has_id(api_gateway_info) is None

    def test_api_gateway_info_has_id_fails_when_missing(self) -> None:
        instance = integration_module.Layer5APIGatewayRegionalTests()
        api_gateway_info: Dict[str, Any] = {}
        with pytest.raises(AssertionError):
            instance.test_api_gateway_info_has_id(api_gateway_info)


class TestLayer6DeploymentCapabilityTestsExecution:
    def test_can_get_lambda_function_configuration_success_with_functions(self) -> None:
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_functions.return_value = {
            "Functions": [{"FunctionName": "my-function"}]
        }
        mock_client.get_function_configuration.return_value = {"FunctionName": "my-function"}
        assert instance.test_can_get_lambda_function_configuration(mock_client) is None
        mock_client.get_function_configuration.assert_called_once()

    def test_can_get_lambda_function_configuration_success_no_functions(self) -> None:
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_functions.return_value = {"Functions": []}
        assert instance.test_can_get_lambda_function_configuration(mock_client) is None
        mock_client.get_function_configuration.assert_not_called()

    def test_can_get_lambda_function_configuration_fails_on_access_denied(self) -> None:
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_functions.return_value = {
            "Functions": [{"FunctionName": "my-function"}]
        }
        mock_client.get_function_configuration.side_effect = create_client_error(
            "AccessDeniedException"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_get_lambda_function_configuration(mock_client)

    def test_can_get_lambda_function_configuration_reraises_other_errors(self) -> None:
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_functions.return_value = {
            "Functions": [{"FunctionName": "my-function"}]
        }
        mock_client.get_function_configuration.side_effect = create_client_error(
            "InternalError"
        )
        with pytest.raises(ClientError):
            instance.test_can_get_lambda_function_configuration(mock_client)

    def test_can_create_log_group_dry_run_success(self) -> None:
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.describe_log_groups.return_value = {"logGroups": []}
        assert instance.test_can_create_log_group_dry_run(mock_client) is None

    def test_can_create_log_group_dry_run_fails_on_access_denied(self) -> None:
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.describe_log_groups.side_effect = create_client_error(
            "AccessDeniedException"
        )
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_create_log_group_dry_run(mock_client)

    def test_can_create_log_group_dry_run_reraises_other_errors(self) -> None:
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.describe_log_groups.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_create_log_group_dry_run(mock_client)

    def test_can_get_iam_role_details_success_with_roles(self) -> None:
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_roles.return_value = {"Roles": [{"RoleName": "my-role"}]}
        mock_client.get_role.return_value = {"Role": {"RoleName": "my-role"}}
        assert instance.test_can_get_iam_role_details(mock_client) is None
        mock_client.get_role.assert_called_once()

    def test_can_get_iam_role_details_success_no_roles(self) -> None:
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_roles.return_value = {"Roles": []}
        assert instance.test_can_get_iam_role_details(mock_client) is None
        mock_client.get_role.assert_not_called()

    def test_can_get_iam_role_details_fails_on_access_denied(self) -> None:
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_roles.return_value = {"Roles": [{"RoleName": "my-role"}]}
        mock_client.get_role.side_effect = create_client_error("AccessDenied")
        with pytest.raises(pytest.fail.Exception):
            instance.test_can_get_iam_role_details(mock_client)

    def test_can_get_iam_role_details_reraises_other_errors(self) -> None:
        instance = integration_module.Layer6DeploymentCapabilityTests()
        mock_client = MagicMock()
        mock_client.list_roles.return_value = {"Roles": [{"RoleName": "my-role"}]}
        mock_client.get_role.side_effect = create_client_error("InternalError")
        with pytest.raises(ClientError):
            instance.test_can_get_iam_role_details(mock_client)
