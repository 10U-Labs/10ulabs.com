"""Shared base classes and factories for 7-layer pre-deployment integration tests.

The 7-layer testing model:
- Layer 1: Contracts - Local file compatibility (openapi.json + templatefile vars)
- Layer 2: Authentication - Valid credentials exist
- Layer 3: Authorization - Permission to inspect resources
- Layer 4: State - Terraform state matches AWS reality
- Layer 5: Existence - Required resources exist
- Layer 6: Configuration - Resources configured correctly
- Layer 7: Capability - Can perform required operations

Usage:
    # In your test file:
    from test_fixtures.integration import Layer2EndpointAuthenticationTests

    class TestAWSAuthentication(Layer2EndpointAuthenticationTests):
        pass  # Inherits all base tests
"""
from test_fixtures.integration.base_classes import (
    Layer1AuthenticationTests,
    Layer1EndpointAuthenticationTests,
    Layer2APIGatewayAuthorizationTests,
    Layer2ECRAuthorizationTests,
    Layer2EndpointAuthenticationTests,
    Layer2IAMAuthorizationTests,
    Layer2LambdaAndIAMAuthorizationTests,
    Layer2S3AuthorizationTests,
    Layer3APIGatewayAuthorizationTests,
    Layer3LambdaAndIAMAuthorizationTests,
    Layer4APIBackendPrerequisiteTests,
    Layer4IAMRoleExistenceTests,
    Layer4PrerequisiteExistenceTests,
    Layer4TerraformStateExistenceTests,
    Layer5APIBackendPrerequisiteTests,
    Layer5APIGatewayRegionalTests,
    Layer5IAMConfigurationTests,
    Layer5PrerequisiteConfigurationTests,
    Layer5S3ConfigurationTests,
    Layer5S3RegionTests,
    Layer6APIGatewayRegionalTests,
    Layer6DeploymentCapabilityTests,
    Layer6ECRCapabilityTests,
    Layer6IAMCapabilityTests,
    Layer6S3CapabilityTests,
    Layer6S3WriteCapabilityTests,
    Layer7DeploymentCapabilityTests,
)
from test_fixtures.integration.factories import (
    create_deployed_naming_convention_tests,
    create_ecs_runner_lambda_existence_tests,
    create_ecs_runner_outputs_tests,
    create_lambda_api_gateway_wiring_tests,
    create_lambda_configuration_tests,
    create_lambda_execution_role_wiring_tests,
    create_lambda_existence_tests,
    create_lambda_iam_wiring_tests,
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
)
from test_fixtures.integration.helpers import (
    assert_api_gateway_exists,
    assert_iam_role_name_is_pascalcase,
    check_s3_head_bucket_permission,
    check_service_can_assume_role,
    check_state_file_readable,
    get_aws_account_id_via_cli,
    handle_ecr_authorization_error,
    skip_if_api_gateway_unavailable,
)

__all__ = [
    # Base classes (7-layer model)
    "Layer2EndpointAuthenticationTests",
    "Layer3APIGatewayAuthorizationTests",
    "Layer3LambdaAndIAMAuthorizationTests",
    "Layer5APIBackendPrerequisiteTests",
    "Layer6APIGatewayRegionalTests",
    "Layer7DeploymentCapabilityTests",
    # Base classes (legacy naming)
    "Layer1AuthenticationTests",
    "Layer1EndpointAuthenticationTests",
    "Layer2APIGatewayAuthorizationTests",
    "Layer2ECRAuthorizationTests",
    "Layer2IAMAuthorizationTests",
    "Layer2LambdaAndIAMAuthorizationTests",
    "Layer2S3AuthorizationTests",
    "Layer4APIBackendPrerequisiteTests",
    "Layer4IAMRoleExistenceTests",
    "Layer4PrerequisiteExistenceTests",
    "Layer4TerraformStateExistenceTests",
    "Layer5APIGatewayRegionalTests",
    "Layer5IAMConfigurationTests",
    "Layer5PrerequisiteConfigurationTests",
    "Layer5S3ConfigurationTests",
    "Layer5S3RegionTests",
    "Layer6DeploymentCapabilityTests",
    "Layer6ECRCapabilityTests",
    "Layer6IAMCapabilityTests",
    "Layer6S3CapabilityTests",
    "Layer6S3WriteCapabilityTests",
    # Factory functions
    "create_deployed_naming_convention_tests",
    "create_ecs_runner_lambda_existence_tests",
    "create_ecs_runner_outputs_tests",
    "create_lambda_api_gateway_wiring_tests",
    "create_lambda_configuration_tests",
    "create_lambda_execution_role_wiring_tests",
    "create_lambda_existence_tests",
    "create_lambda_iam_wiring_tests",
    "create_log_group_configuration_tests",
    "create_naming_convention_tests",
    "create_layer1_authentication_tests",
    "create_layer2_s3_authorization_tests",
    "create_layer6_capability_tests",
    "create_security_group_existence_test",
    "create_simple_layer1_authentication_tests",
    "create_sqs_fifo_queue_tests",
    "create_www_common_fixtures",
    "create_www_common_s3_existence_tests",
    "handle_ecr_error",
    # Helper functions
    "assert_api_gateway_exists",
    "assert_iam_role_name_is_pascalcase",
    "check_s3_head_bucket_permission",
    "check_service_can_assume_role",
    "check_state_file_readable",
    "get_aws_account_id_via_cli",
    "handle_ecr_authorization_error",
    "skip_if_api_gateway_unavailable",
]
