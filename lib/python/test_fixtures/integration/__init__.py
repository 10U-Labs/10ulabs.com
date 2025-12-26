"""Shared base classes and factories for 7-layer pre-deployment integration tests.

The 7-layer testing model:
- Layer 1: Contracts - Local file compatibility (openapi.json + templatefile vars)
- Layer 2: Authentication - Valid credentials exist
- Layer 3: Authorization - Permission to inspect resources
- Layer 4: State - Terraform state matches AWS reality
- Layer 5: Existence - Required resources exist
- Layer 6: Configuration - Resources configured correctly
- Layer 7: Capability - Can perform required operations

Note: Base classes are named Layer1-Layer6 for backward compatibility with existing
tests. New tests should use the 7-layer pytestmark numbering (Layer 1 = Contracts).

Usage:
    # In your test file:
    from test_fixtures.integration import Layer1AuthenticationTests

    class TestAWSAuthentication(Layer1AuthenticationTests):
        pass  # Inherits all base tests
"""
from test_fixtures.integration.base_classes import (
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
)
from test_fixtures.integration.factories import (
    create_ecs_runner_lambda_existence_tests,
    create_ecs_runner_outputs_tests,
    create_lambda_api_gateway_wiring_tests,
    create_lambda_execution_role_wiring_tests,
    create_lambda_existence_tests,
    create_lambda_iam_wiring_tests,
    create_layer1_authentication_tests,
    create_layer2_s3_authorization_tests,
    create_layer6_capability_tests,
    create_security_group_existence_test,
    create_simple_layer1_authentication_tests,
    create_sqs_fifo_queue_tests,
    create_www_shared_fixtures,
    create_www_shared_s3_existence_tests,
    handle_ecr_error,
)
from test_fixtures.integration.helpers import (
    check_service_can_assume_role,
    get_aws_account_id_via_cli,
    handle_ecr_authorization_error,
)

__all__ = [
    # Base classes
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
    "create_ecs_runner_lambda_existence_tests",
    "create_ecs_runner_outputs_tests",
    "create_lambda_api_gateway_wiring_tests",
    "create_lambda_execution_role_wiring_tests",
    "create_lambda_existence_tests",
    "create_lambda_iam_wiring_tests",
    "create_layer1_authentication_tests",
    "create_layer2_s3_authorization_tests",
    "create_layer6_capability_tests",
    "create_security_group_existence_test",
    "create_simple_layer1_authentication_tests",
    "create_sqs_fifo_queue_tests",
    "create_www_shared_fixtures",
    "create_www_shared_s3_existence_tests",
    "handle_ecr_error",
    # Helper functions
    "check_service_can_assume_role",
    "get_aws_account_id_via_cli",
    "handle_ecr_authorization_error",
]
