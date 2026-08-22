"""Unit tests for test_fixtures.integration module imports."""
from test_fixtures.integration import (
    # Base classes (7-layer model)
    Layer2EndpointAuthenticationTests,
    Layer3APIGatewayAuthorizationTests,
    Layer3LambdaAndIAMAuthorizationTests,
    Layer5APIBackendPrerequisiteTests,
    Layer6APIGatewayRegionalTests,
    Layer7DeploymentCapabilityTests,
    # Base classes (legacy naming)
    Layer1AuthenticationTests,
    Layer1EndpointAuthenticationTests,
    Layer2APIGatewayAuthorizationTests,
    Layer2ECRAuthorizationTests,
    Layer2IAMAuthorizationTests,
    Layer2LambdaAndIAMAuthorizationTests,
    Layer2S3AuthorizationTests,
    Layer4APIBackendPrerequisiteTests,
    Layer4IAMRoleExistenceTests,
    Layer4PrerequisiteExistenceTests,
    Layer4TerraformStateExistenceTests,
    Layer5APIGatewayRegionalTests,
    Layer5IAMConfigurationTests,
    Layer5PrerequisiteConfigurationTests,
    Layer5S3ConfigurationTests,
    Layer5S3RegionTests,
    Layer6DeploymentCapabilityTests,
    Layer6ECRCapabilityTests,
    Layer6IAMCapabilityTests,
    Layer6S3CapabilityTests,
    Layer6S3WriteCapabilityTests,
    # Factory functions
    create_deployed_naming_convention_tests,
    create_kms_policy_test,
    create_lambda_api_gateway_wiring_tests,
    create_lambda_configuration_tests,
    create_lambda_execution_role_wiring_tests,
    create_lambda_existence_tests,
    create_lambda_iam_wiring_tests,
    create_lambda_role_existence_test,
    create_layer1_authentication_tests,
    create_layer2_s3_authorization_tests,
    create_layer6_capability_tests,
    create_log_group_configuration_tests,
    create_naming_convention_tests,
    create_security_group_existence_test,
    create_simple_layer1_authentication_tests,
    create_sqs_fifo_queue_tests,
    create_www_common_fixtures,
    create_www_common_s3_existence_tests,
    handle_ecr_error,
    # Helper functions
    assert_api_gateway_exists,
    assert_iam_role_name_is_pascalcase,
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


# === Base Classes Imports ===


def test_layer1_authentication_tests_import():
    """Layer1AuthenticationTests is importable."""
    assert Layer1AuthenticationTests is not None


def test_layer1_endpoint_authentication_tests_import():
    """Layer1EndpointAuthenticationTests is importable."""
    assert Layer1EndpointAuthenticationTests is not None


def test_layer2_api_gateway_authorization_tests_import():
    """Layer2APIGatewayAuthorizationTests is importable."""
    assert Layer2APIGatewayAuthorizationTests is not None


def test_layer2_ecr_authorization_tests_import():
    """Layer2ECRAuthorizationTests is importable."""
    assert Layer2ECRAuthorizationTests is not None


def test_layer2_endpoint_authentication_tests_import():
    """Layer2EndpointAuthenticationTests is importable."""
    assert Layer2EndpointAuthenticationTests is not None


def test_layer2_iam_authorization_tests_import():
    """Layer2IAMAuthorizationTests is importable."""
    assert Layer2IAMAuthorizationTests is not None


def test_layer2_lambda_and_iam_authorization_tests_import():
    """Layer2LambdaAndIAMAuthorizationTests is importable."""
    assert Layer2LambdaAndIAMAuthorizationTests is not None


def test_layer2_s3_authorization_tests_import():
    """Layer2S3AuthorizationTests is importable."""
    assert Layer2S3AuthorizationTests is not None


def test_layer3_api_gateway_authorization_tests_import():
    """Layer3APIGatewayAuthorizationTests is importable."""
    assert Layer3APIGatewayAuthorizationTests is not None


def test_layer3_lambda_and_iam_authorization_tests_import():
    """Layer3LambdaAndIAMAuthorizationTests is importable."""
    assert Layer3LambdaAndIAMAuthorizationTests is not None


def test_layer4_api_backend_prerequisite_tests_import():
    """Layer4APIBackendPrerequisiteTests is importable."""
    assert Layer4APIBackendPrerequisiteTests is not None


def test_layer4_iam_role_existence_tests_import():
    """Layer4IAMRoleExistenceTests is importable."""
    assert Layer4IAMRoleExistenceTests is not None


def test_layer4_prerequisite_existence_tests_import():
    """Layer4PrerequisiteExistenceTests is importable."""
    assert Layer4PrerequisiteExistenceTests is not None


def test_layer4_terraform_state_existence_tests_import():
    """Layer4TerraformStateExistenceTests is importable."""
    assert Layer4TerraformStateExistenceTests is not None


def test_layer5_api_backend_prerequisite_tests_import():
    """Layer5APIBackendPrerequisiteTests is importable."""
    assert Layer5APIBackendPrerequisiteTests is not None


def test_layer5_api_gateway_regional_tests_import():
    """Layer5APIGatewayRegionalTests is importable."""
    assert Layer5APIGatewayRegionalTests is not None


def test_layer5_iam_configuration_tests_import():
    """Layer5IAMConfigurationTests is importable."""
    assert Layer5IAMConfigurationTests is not None


def test_layer5_prerequisite_configuration_tests_import():
    """Layer5PrerequisiteConfigurationTests is importable."""
    assert Layer5PrerequisiteConfigurationTests is not None


def test_layer5_s3_configuration_tests_import():
    """Layer5S3ConfigurationTests is importable."""
    assert Layer5S3ConfigurationTests is not None


def test_layer5_s3_region_tests_import():
    """Layer5S3RegionTests is importable."""
    assert Layer5S3RegionTests is not None


def test_layer6_api_gateway_regional_tests_import():
    """Layer6APIGatewayRegionalTests is importable."""
    assert Layer6APIGatewayRegionalTests is not None


def test_layer6_deployment_capability_tests_import():
    """Layer6DeploymentCapabilityTests is importable."""
    assert Layer6DeploymentCapabilityTests is not None


def test_layer6_ecr_capability_tests_import():
    """Layer6ECRCapabilityTests is importable."""
    assert Layer6ECRCapabilityTests is not None


def test_layer6_iam_capability_tests_import():
    """Layer6IAMCapabilityTests is importable."""
    assert Layer6IAMCapabilityTests is not None


def test_layer6_s3_capability_tests_import():
    """Layer6S3CapabilityTests is importable."""
    assert Layer6S3CapabilityTests is not None


def test_layer6_s3_write_capability_tests_import():
    """Layer6S3WriteCapabilityTests is importable."""
    assert Layer6S3WriteCapabilityTests is not None


def test_layer7_deployment_capability_tests_import():
    """Layer7DeploymentCapabilityTests is importable."""
    assert Layer7DeploymentCapabilityTests is not None


# === Factory Function Imports ===


def test_create_deployed_naming_convention_tests_import():
    """create_deployed_naming_convention_tests is callable."""
    assert callable(create_deployed_naming_convention_tests)


def test_create_kms_policy_test_import():
    """create_kms_policy_test is callable."""
    assert callable(create_kms_policy_test)


def test_create_lambda_api_gateway_wiring_tests_import():
    """create_lambda_api_gateway_wiring_tests is callable."""
    assert callable(create_lambda_api_gateway_wiring_tests)


def test_create_lambda_configuration_tests_import():
    """create_lambda_configuration_tests is callable."""
    assert callable(create_lambda_configuration_tests)


def test_create_lambda_execution_role_wiring_tests_import():
    """create_lambda_execution_role_wiring_tests is callable."""
    assert callable(create_lambda_execution_role_wiring_tests)


def test_create_lambda_existence_tests_import():
    """create_lambda_existence_tests is callable."""
    assert callable(create_lambda_existence_tests)


def test_create_lambda_iam_wiring_tests_import():
    """create_lambda_iam_wiring_tests is callable."""
    assert callable(create_lambda_iam_wiring_tests)


def test_create_lambda_role_existence_test_import():
    """create_lambda_role_existence_test is callable."""
    assert callable(create_lambda_role_existence_test)


def test_create_layer1_authentication_tests_import():
    """create_layer1_authentication_tests is callable."""
    assert callable(create_layer1_authentication_tests)


def test_create_layer2_s3_authorization_tests_import():
    """create_layer2_s3_authorization_tests is callable."""
    assert callable(create_layer2_s3_authorization_tests)


def test_create_layer6_capability_tests_import():
    """create_layer6_capability_tests is callable."""
    assert callable(create_layer6_capability_tests)


def test_create_log_group_configuration_tests_import():
    """create_log_group_configuration_tests is callable."""
    assert callable(create_log_group_configuration_tests)


def test_create_naming_convention_tests_import():
    """create_naming_convention_tests is callable."""
    assert callable(create_naming_convention_tests)


def test_create_security_group_existence_test_import():
    """create_security_group_existence_test is callable."""
    assert callable(create_security_group_existence_test)


def test_create_simple_layer1_authentication_tests_import():
    """create_simple_layer1_authentication_tests is callable."""
    assert callable(create_simple_layer1_authentication_tests)


def test_create_sqs_fifo_queue_tests_import():
    """create_sqs_fifo_queue_tests is callable."""
    assert callable(create_sqs_fifo_queue_tests)


def test_create_www_common_fixtures_import():
    """create_www_common_fixtures is callable."""
    assert callable(create_www_common_fixtures)


def test_create_www_common_s3_existence_tests_import():
    """create_www_common_s3_existence_tests is callable."""
    assert callable(create_www_common_s3_existence_tests)


def test_handle_ecr_error_import():
    """handle_ecr_error is callable."""
    assert callable(handle_ecr_error)


# === Helper Function Imports ===


def test_assert_api_gateway_exists_import():
    """assert_api_gateway_exists is callable."""
    assert callable(assert_api_gateway_exists)


def test_assert_iam_role_name_is_pascalcase_import():
    """assert_iam_role_name_is_pascalcase is callable."""
    assert callable(assert_iam_role_name_is_pascalcase)


def test_check_iam_role_exists_import():
    """check_iam_role_exists is callable."""
    assert callable(check_iam_role_exists)


def test_check_lambda_function_exists_import():
    """check_lambda_function_exists is callable."""
    assert callable(check_lambda_function_exists)


def test_check_lambda_role_has_policy_import():
    """check_lambda_role_has_policy is callable."""
    assert callable(check_lambda_role_has_policy)


def test_check_s3_head_bucket_permission_import():
    """check_s3_head_bucket_permission is callable."""
    assert callable(check_s3_head_bucket_permission)


def test_check_service_can_assume_role_import():
    """check_service_can_assume_role is callable."""
    assert callable(check_service_can_assume_role)


def test_check_state_file_readable_import():
    """check_state_file_readable is callable."""
    assert callable(check_state_file_readable)


def test_get_aws_account_id_via_cli_import():
    """get_aws_account_id_via_cli is callable."""
    assert callable(get_aws_account_id_via_cli)


def test_handle_ecr_authorization_error_import():
    """handle_ecr_authorization_error is callable."""
    assert callable(handle_ecr_authorization_error)


def test_skip_if_api_gateway_unavailable_import():
    """skip_if_api_gateway_unavailable is callable."""
    assert callable(skip_if_api_gateway_unavailable)
