"""Layer 4: Existence tests for rack_designer endpoint pre-deployment.

Tests that prerequisite resources from OTHER workflows exist.
Not configuration, not capability - just existence.

Six-layer testing model:
- Layer 4: Existence - Prerequisite resources actually exist
"""

import pytest
from test_fixtures.integration import (
    assert_api_gateway_exists,
    create_ecs_runner_outputs_tests,
    create_ecs_runner_lambda_existence_tests,
    create_www_shared_s3_existence_tests,
)


pytestmark = pytest.mark.layer(4)


class TestAPIBackendPrerequisites:
    """Layer 4: Verify api_shared_routing resources exist."""

    def test_api_shared_routing_outputs_provides_gateway_id(self, api_shared_routing_outputs):
        """Verify api_shared_routing terraform outputs provide api_gateway_id."""
        assert api_shared_routing_outputs.get("api_gateway_id"), (
            "api_gateway_id output not found in api_shared_routing. "
            "Run terraform apply in src/api/shared/routing/"
        )

    def test_api_gateway_rest_api_exists(self, api_gateway_info):
        """Verify the API Gateway REST API exists."""
        assert_api_gateway_exists(api_gateway_info)


TestECSRunnerOutputs = create_ecs_runner_outputs_tests()
TestECSRunnerLambdaExistence = create_ecs_runner_lambda_existence_tests()
TestWWWSharedPrerequisites = create_www_shared_s3_existence_tests()
