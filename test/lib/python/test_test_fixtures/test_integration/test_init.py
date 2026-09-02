from test_fixtures.integration import (
    Layer2EndpointAuthenticationTests,
    Layer3APIGatewayAuthorizationTests,
    Layer3LambdaAndIAMAuthorizationTests,
    Layer5APIBackendPrerequisiteTests,
    Layer6APIGatewayRegionalTests,
    Layer7DeploymentCapabilityTests,
    Layer1EndpointAuthenticationTests,
    Layer2APIGatewayAuthorizationTests,
    Layer2IAMAuthorizationTests,
    Layer2LambdaAndIAMAuthorizationTests,
    Layer2S3AuthorizationTests,
    Layer4APIBackendPrerequisiteTests,
    Layer4IAMRoleExistenceTests,
    Layer4TerraformStateExistenceTests,
    Layer5APIGatewayRegionalTests,
    Layer5IAMConfigurationTests,
    Layer6DeploymentCapabilityTests,
    Layer6IAMCapabilityTests,
    Layer6S3CapabilityTests,
    Layer6S3WriteCapabilityTests,
    create_deployed_resource_existence_tests,
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
    create_security_group_existence_test,
    create_simple_layer1_authentication_tests,
    create_sqs_fifo_queue_tests,
    create_www_common_fixtures,
    create_www_common_s3_existence_tests,
    handle_ecr_error,
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


def test_layer1_endpoint_authentication_tests_import() -> None:
    assert Layer1EndpointAuthenticationTests is not None


def test_layer2_api_gateway_authorization_tests_import() -> None:
    assert Layer2APIGatewayAuthorizationTests is not None


def test_layer2_endpoint_authentication_tests_import() -> None:
    assert Layer2EndpointAuthenticationTests is not None


def test_layer2_iam_authorization_tests_import() -> None:
    assert Layer2IAMAuthorizationTests is not None


def test_layer2_lambda_and_iam_authorization_tests_import() -> None:
    assert Layer2LambdaAndIAMAuthorizationTests is not None


def test_layer2_s3_authorization_tests_import() -> None:
    assert Layer2S3AuthorizationTests is not None


def test_layer3_api_gateway_authorization_tests_import() -> None:
    assert Layer3APIGatewayAuthorizationTests is not None


def test_layer3_lambda_and_iam_authorization_tests_import() -> None:
    assert Layer3LambdaAndIAMAuthorizationTests is not None


def test_layer4_api_backend_prerequisite_tests_import() -> None:
    assert Layer4APIBackendPrerequisiteTests is not None


def test_layer4_iam_role_existence_tests_import() -> None:
    assert Layer4IAMRoleExistenceTests is not None


def test_layer4_terraform_state_existence_tests_import() -> None:
    assert Layer4TerraformStateExistenceTests is not None


def test_layer5_api_backend_prerequisite_tests_import() -> None:
    assert Layer5APIBackendPrerequisiteTests is not None


def test_layer5_api_gateway_regional_tests_import() -> None:
    assert Layer5APIGatewayRegionalTests is not None


def test_layer5_iam_configuration_tests_import() -> None:
    assert Layer5IAMConfigurationTests is not None


def test_layer6_api_gateway_regional_tests_import() -> None:
    assert Layer6APIGatewayRegionalTests is not None


def test_layer6_deployment_capability_tests_import() -> None:
    assert Layer6DeploymentCapabilityTests is not None


def test_layer6_iam_capability_tests_import() -> None:
    assert Layer6IAMCapabilityTests is not None


def test_layer6_s3_capability_tests_import() -> None:
    assert Layer6S3CapabilityTests is not None


def test_layer6_s3_write_capability_tests_import() -> None:
    assert Layer6S3WriteCapabilityTests is not None


def test_layer7_deployment_capability_tests_import() -> None:
    assert Layer7DeploymentCapabilityTests is not None


def test_create_deployed_resource_existence_tests_import() -> None:
    assert callable(create_deployed_resource_existence_tests)


def test_create_kms_policy_test_import() -> None:
    assert callable(create_kms_policy_test)


def test_create_lambda_api_gateway_wiring_tests_import() -> None:
    assert callable(create_lambda_api_gateway_wiring_tests)


def test_create_lambda_configuration_tests_import() -> None:
    assert callable(create_lambda_configuration_tests)


def test_create_lambda_execution_role_wiring_tests_import() -> None:
    assert callable(create_lambda_execution_role_wiring_tests)


def test_create_lambda_existence_tests_import() -> None:
    assert callable(create_lambda_existence_tests)


def test_create_lambda_iam_wiring_tests_import() -> None:
    assert callable(create_lambda_iam_wiring_tests)


def test_create_lambda_role_existence_test_import() -> None:
    assert callable(create_lambda_role_existence_test)


def test_create_layer1_authentication_tests_import() -> None:
    assert callable(create_layer1_authentication_tests)


def test_create_layer2_s3_authorization_tests_import() -> None:
    assert callable(create_layer2_s3_authorization_tests)


def test_create_layer6_capability_tests_import() -> None:
    assert callable(create_layer6_capability_tests)


def test_create_log_group_configuration_tests_import() -> None:
    assert callable(create_log_group_configuration_tests)


def test_create_security_group_existence_test_import() -> None:
    assert callable(create_security_group_existence_test)


def test_create_simple_layer1_authentication_tests_import() -> None:
    assert callable(create_simple_layer1_authentication_tests)


def test_create_sqs_fifo_queue_tests_import() -> None:
    assert callable(create_sqs_fifo_queue_tests)


def test_create_www_common_fixtures_import() -> None:
    assert callable(create_www_common_fixtures)


def test_create_www_common_s3_existence_tests_import() -> None:
    assert callable(create_www_common_s3_existence_tests)


def test_handle_ecr_error_import() -> None:
    assert callable(handle_ecr_error)


def test_assert_api_gateway_exists_import() -> None:
    assert callable(assert_api_gateway_exists)


def test_check_iam_role_exists_import() -> None:
    assert callable(check_iam_role_exists)


def test_check_lambda_function_exists_import() -> None:
    assert callable(check_lambda_function_exists)


def test_check_lambda_role_has_policy_import() -> None:
    assert callable(check_lambda_role_has_policy)


def test_check_s3_head_bucket_permission_import() -> None:
    assert callable(check_s3_head_bucket_permission)


def test_check_service_can_assume_role_import() -> None:
    assert callable(check_service_can_assume_role)


def test_check_state_file_readable_import() -> None:
    assert callable(check_state_file_readable)


def test_get_aws_account_id_via_cli_import() -> None:
    assert callable(get_aws_account_id_via_cli)


def test_handle_ecr_authorization_error_import() -> None:
    assert callable(handle_ecr_authorization_error)


def test_skip_if_api_gateway_unavailable_import() -> None:
    assert callable(skip_if_api_gateway_unavailable)
