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
    """Layer 4: Verify api_backend prerequisites exist."""

    pass  # All tests inherited from base class


class TestECSRunnerPrerequisites:
    """Layer 4: Verify ecs_runner prerequisites exist."""

    def test_task_definition_arn_output_exists(self, ecs_runner_outputs):
        """Verify task_definition_arn output is available."""
        assert ecs_runner_outputs.get("task_definition_arn"), (
            "task_definition_arn output not found in ecs_runner. "
            "Run terraform apply in src/api/endpoints/ecs_runner/"
        )


TestECSRunnerOutputs = create_ecs_runner_outputs_tests()
TestECSRunnerLambdaExistence = create_ecs_runner_lambda_existence_tests()
