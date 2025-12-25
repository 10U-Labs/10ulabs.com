"""Tests to validate ECS runner infrastructure exists for simulation_soc endpoint.

Five-layer testing model:
- Layer 3: Existence - Do the ECS runner resources exist?

These tests verify that ecs_runner resources this endpoint depends on exist.
"""

from test_fixtures.integration import (
    create_ecs_runner_outputs_tests,
    create_ecs_runner_lambda_existence_tests,
)


TestECSRunnerOutputs = create_ecs_runner_outputs_tests()
TestECSRunnerLambdaExistence = create_ecs_runner_lambda_existence_tests()
