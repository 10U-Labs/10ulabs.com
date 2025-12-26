"""Layer 4: Existence tests for diagnostics endpoint pre-deployment.

Tests that prerequisite resources exist. Assumes authorization passed.
These tests verify that resources from OTHER workflows that THIS workflow
depends on exist before deployment.

Six-layer testing model:
- Layer 4: Existence - Prerequisite resources exist
"""

import pytest
from test_fixtures.integration import (
    Layer4APIBackendPrerequisiteTests,
    create_ecs_runner_outputs_tests,
    create_ecs_runner_lambda_existence_tests,
)


pytestmark = pytest.mark.layer(4)


class TestAPIBackendPrerequisites(Layer4APIBackendPrerequisiteTests):
    """Layer 4: Verify api_shared_routing prerequisites exist.

    All tests inherited from Layer4APIBackendPrerequisiteTests.
    """


# Use factory-created test classes for ecs_runner tests
# These factories include tests for task_definition_arn, cluster_arn,
# cluster_name, and lambda_function_name outputs
TestECSRunnerOutputs = create_ecs_runner_outputs_tests()
TestECSRunnerLambdaExistence = create_ecs_runner_lambda_existence_tests()
