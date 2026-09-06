from typing import Any

import test_fixtures.integration as integration_module


def _get_class(name: str) -> Any:
    return getattr(integration_module, name)


Layer1EndpointAuthenticationTests = _get_class("Layer1EndpointAuthenticationTests")
Layer2APIGatewayAuthorizationTests = _get_class("Layer2APIGatewayAuthorizationTests")
Layer2EndpointAuthenticationTests = _get_class("Layer2EndpointAuthenticationTests")
Layer2IAMAuthorizationTests = _get_class("Layer2IAMAuthorizationTests")
Layer2LambdaAndIAMAuthorizationTests = _get_class("Layer2LambdaAndIAMAuthorizationTests")
Layer2S3AuthorizationTests = _get_class("Layer2S3AuthorizationTests")
Layer3APIGatewayAuthorizationTests = _get_class("Layer3APIGatewayAuthorizationTests")
Layer3LambdaAndIAMAuthorizationTests = _get_class("Layer3LambdaAndIAMAuthorizationTests")
Layer4APIBackendPrerequisiteTests = _get_class("Layer4APIBackendPrerequisiteTests")
Layer4IAMRoleExistenceTests = _get_class("Layer4IAMRoleExistenceTests")
Layer4TerraformStateExistenceTests = _get_class("Layer4TerraformStateExistenceTests")
Layer5APIBackendPrerequisiteTests = _get_class("Layer5APIBackendPrerequisiteTests")
Layer5APIGatewayRegionalTests = _get_class("Layer5APIGatewayRegionalTests")
Layer5IAMConfigurationTests = _get_class("Layer5IAMConfigurationTests")
Layer6APIGatewayRegionalTests = _get_class("Layer6APIGatewayRegionalTests")
Layer6DeploymentCapabilityTests = _get_class("Layer6DeploymentCapabilityTests")
Layer6IAMCapabilityTests = _get_class("Layer6IAMCapabilityTests")
Layer6S3CapabilityTests = _get_class("Layer6S3CapabilityTests")
Layer6S3WriteCapabilityTests = _get_class("Layer6S3WriteCapabilityTests")
Layer7DeploymentCapabilityTests = _get_class("Layer7DeploymentCapabilityTests")


def test_layer2_iam_authorization_tests_class_exists() -> None:
    assert Layer2IAMAuthorizationTests is not None


def test_has_can_call_iam_get_role_api_test() -> None:
    assert hasattr(Layer2IAMAuthorizationTests, "test_can_call_iam_get_role_api")


def test_has_can_list_attached_policies_test() -> None:
    assert hasattr(Layer2IAMAuthorizationTests, "test_can_list_attached_policies")


def test_layer2_s3_authorization_tests_class_exists() -> None:
    assert Layer2S3AuthorizationTests is not None


def test_has_can_call_s3_head_bucket_api_test() -> None:
    assert hasattr(Layer2S3AuthorizationTests, "test_can_call_s3_head_bucket_api")


def test_has_state_bucket_name_configured_test() -> None:
    assert hasattr(Layer2S3AuthorizationTests, "test_state_bucket_name_configured")


def test_layer4_terraform_state_existence_tests_class_exists() -> None:
    assert Layer4TerraformStateExistenceTests is not None


def test_has_state_bucket_exists_test() -> None:
    assert hasattr(Layer4TerraformStateExistenceTests, "test_state_bucket_exists")


def test_has_state_bucket_has_name_test() -> None:
    assert hasattr(Layer4TerraformStateExistenceTests, "test_state_bucket_has_name")


def test_layer6_s3_capability_tests_class_exists() -> None:
    assert Layer6S3CapabilityTests is not None


def test_has_can_list_bucket_objects_test() -> None:
    assert hasattr(Layer6S3CapabilityTests, "test_can_list_bucket_objects")


def test_has_can_get_bucket_location_test() -> None:
    assert hasattr(Layer6S3CapabilityTests, "test_can_get_bucket_location")


def test_layer4_iam_role_existence_tests_class_exists() -> None:
    assert Layer4IAMRoleExistenceTests is not None


def test_has_iam_role_exists_test() -> None:
    assert hasattr(Layer4IAMRoleExistenceTests, "test_iam_role_exists")


def test_has_current_role_name_is_configured_test() -> None:
    assert hasattr(
        Layer4IAMRoleExistenceTests, "test_current_role_name_is_configured"
    )


def test_layer5_iam_configuration_tests_class_exists() -> None:
    assert Layer5IAMConfigurationTests is not None


def test_has_role_has_administrator_access_policy_test() -> None:
    assert hasattr(
        Layer5IAMConfigurationTests, "test_role_has_administrator_access_policy"
    )


def test_has_role_has_at_least_one_policy_test() -> None:
    assert hasattr(
        Layer5IAMConfigurationTests, "test_role_has_at_least_one_policy"
    )


def test_layer6_iam_capability_tests_class_exists() -> None:
    assert Layer6IAMCapabilityTests is not None


def test_has_can_list_buckets_test() -> None:
    assert hasattr(Layer6IAMCapabilityTests, "test_can_list_buckets")


def test_layer6_iam_capability_tests_has_can_list_roles_test() -> None:
    assert hasattr(Layer6IAMCapabilityTests, "test_can_list_roles")


def test_layer6_s3_write_capability_tests_class_exists() -> None:
    assert Layer6S3WriteCapabilityTests is not None


def test_has_can_write_to_bucket_test() -> None:
    assert hasattr(Layer6S3WriteCapabilityTests, "test_can_write_to_bucket")


def test_has_can_delete_from_bucket_test() -> None:
    assert hasattr(Layer6S3WriteCapabilityTests, "test_can_delete_from_bucket")


def test_layer1_endpoint_authentication_tests_class_exists() -> None:
    assert Layer1EndpointAuthenticationTests is not None


def test_has_aws_credentials_are_valid_test() -> None:
    assert hasattr(
        Layer1EndpointAuthenticationTests, "test_aws_credentials_are_valid"
    )


def test_has_aws_credentials_return_account_id_test() -> None:
    assert hasattr(
        Layer1EndpointAuthenticationTests, "test_aws_credentials_return_account_id"
    )


def test_has_aws_credentials_return_arn_test() -> None:
    assert hasattr(
        Layer1EndpointAuthenticationTests, "test_aws_credentials_return_arn"
    )


def test_has_aws_credentials_arn_has_valid_format_test() -> None:
    assert hasattr(
        Layer1EndpointAuthenticationTests, "test_aws_credentials_arn_has_valid_format"
    )


def test_layer2_api_gateway_authorization_tests_class_exists() -> None:
    assert Layer2APIGatewayAuthorizationTests is not None


def test_has_can_describe_rest_apis_test() -> None:
    assert hasattr(
        Layer2APIGatewayAuthorizationTests, "test_can_describe_rest_apis"
    )


def test_has_can_access_specific_rest_api_test() -> None:
    assert hasattr(
        Layer2APIGatewayAuthorizationTests, "test_can_access_specific_rest_api"
    )


def test_layer2_lambda_and_iam_authorization_tests_class_exists() -> None:
    assert Layer2LambdaAndIAMAuthorizationTests is not None


def test_has_can_list_functions_test() -> None:
    assert hasattr(Layer2LambdaAndIAMAuthorizationTests, "test_can_list_functions")


def test_layer2_lambda_and_iam_authorization_tests_has_can_list_roles_test() -> None:
    assert hasattr(Layer2LambdaAndIAMAuthorizationTests, "test_can_list_roles")


def test_layer4_api_backend_prerequisite_tests_class_exists() -> None:
    assert Layer4APIBackendPrerequisiteTests is not None


def test_has_api_gateway_id_output_exists_test() -> None:
    assert hasattr(
        Layer4APIBackendPrerequisiteTests, "test_api_gateway_id_output_exists"
    )


def test_has_api_gateway_exists_in_aws_test() -> None:
    assert hasattr(
        Layer4APIBackendPrerequisiteTests, "test_api_gateway_exists_in_aws"
    )


def test_layer5_api_gateway_regional_tests_class_exists() -> None:
    assert Layer5APIGatewayRegionalTests is not None


def test_has_api_gateway_is_regional_test() -> None:
    assert hasattr(Layer5APIGatewayRegionalTests, "test_api_gateway_is_regional")


def test_has_api_gateway_info_has_id_test() -> None:
    assert hasattr(Layer5APIGatewayRegionalTests, "test_api_gateway_info_has_id")


def test_layer6_deployment_capability_tests_class_exists() -> None:
    assert Layer6DeploymentCapabilityTests is not None


def test_has_can_get_lambda_function_configuration_test() -> None:
    assert hasattr(
        Layer6DeploymentCapabilityTests, "test_can_get_lambda_function_configuration"
    )


def test_has_can_create_log_group_dry_run_test() -> None:
    assert hasattr(
        Layer6DeploymentCapabilityTests, "test_can_create_log_group_dry_run"
    )


def test_has_can_get_iam_role_details_test() -> None:
    assert hasattr(
        Layer6DeploymentCapabilityTests, "test_can_get_iam_role_details"
    )


def test_layer2_endpoint_authentication_tests_alias() -> None:
    assert Layer2EndpointAuthenticationTests is Layer1EndpointAuthenticationTests


def test_layer3_api_gateway_authorization_tests_alias() -> None:
    assert Layer3APIGatewayAuthorizationTests is Layer2APIGatewayAuthorizationTests


def test_layer3_lambda_and_iam_authorization_tests_alias() -> None:
    assert (
        Layer3LambdaAndIAMAuthorizationTests is Layer2LambdaAndIAMAuthorizationTests
    )


def test_layer5_api_backend_prerequisite_tests_alias() -> None:
    assert Layer5APIBackendPrerequisiteTests is Layer4APIBackendPrerequisiteTests


def test_layer6_api_gateway_regional_tests_alias() -> None:
    assert Layer6APIGatewayRegionalTests is Layer5APIGatewayRegionalTests


def test_layer7_deployment_capability_tests_alias() -> None:
    assert Layer7DeploymentCapabilityTests is Layer6DeploymentCapabilityTests
