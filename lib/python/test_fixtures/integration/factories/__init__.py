"""Factory functions for creating test classes.

These functions dynamically create test classes with specific configurations.
"""
from test_fixtures.integration.factories.authentication import (
    create_layer1_authentication_tests,
    create_layer2_s3_authorization_tests,
    create_simple_layer1_authentication_tests,
)
from test_fixtures.integration.factories.capability import (
    create_layer6_capability_tests,
)
from test_fixtures.integration.factories.infrastructure import (
    create_ecs_runner_lambda_existence_tests,
    create_ecs_runner_outputs_tests,
    create_log_group_configuration_tests,
    create_security_group_existence_test,
    create_sqs_fifo_queue_tests,
    create_www_common_fixtures,
    create_www_common_s3_existence_tests,
    handle_ecr_error,
)
from test_fixtures.integration.factories.lambda_factories import (
    create_deployed_naming_convention_tests,
    create_lambda_api_gateway_wiring_tests,
    create_lambda_configuration_tests,
    create_lambda_execution_role_wiring_tests,
    create_lambda_existence_tests,
    create_lambda_iam_wiring_tests,
    create_naming_convention_tests,
)

__all__ = [
    # Authentication
    "create_layer1_authentication_tests",
    "create_layer2_s3_authorization_tests",
    "create_simple_layer1_authentication_tests",
    # Capability
    "create_layer6_capability_tests",
    # Infrastructure
    "create_ecs_runner_lambda_existence_tests",
    "create_ecs_runner_outputs_tests",
    "create_log_group_configuration_tests",
    "create_security_group_existence_test",
    "create_sqs_fifo_queue_tests",
    "create_www_common_fixtures",
    "create_www_common_s3_existence_tests",
    "handle_ecr_error",
    # Lambda
    "create_deployed_naming_convention_tests",
    "create_lambda_api_gateway_wiring_tests",
    "create_lambda_configuration_tests",
    "create_lambda_execution_role_wiring_tests",
    "create_lambda_existence_tests",
    "create_lambda_iam_wiring_tests",
    "create_naming_convention_tests",
]
