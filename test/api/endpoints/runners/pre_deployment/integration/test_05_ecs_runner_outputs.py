"""Tests to validate ecs_runner infrastructure exists."""
import pytest


def test_ecs_runner_has_lambda_function_arn_output(ecs_runner_outputs):
    """Verify ecs_runner has lambda_function_arn output."""
    assert ecs_runner_outputs.get("lambda_function_arn"), \
        "lambda_function_arn output not found in ecs_runner"


def test_ecs_runner_has_lambda_function_name_output(ecs_runner_outputs):
    """Verify ecs_runner has lambda_function_name output."""
    assert ecs_runner_outputs.get("lambda_function_name"), \
        "lambda_function_name output not found in ecs_runner"


def test_ecs_runner_has_cluster_arn_output(ecs_runner_outputs):
    """Verify ecs_runner has cluster_arn output."""
    assert ecs_runner_outputs.get("cluster_arn"), \
        "cluster_arn output not found in ecs_runner"


def test_ecs_runner_has_cluster_name_output(ecs_runner_outputs):
    """Verify ecs_runner has cluster_name output."""
    assert ecs_runner_outputs.get("cluster_name"), \
        "cluster_name output not found in ecs_runner"


def test_ecs_runner_lambda_function_name_available(ecs_runner_outputs):
    """Verify lambda_function_name output is available for lookup."""
    function_name = ecs_runner_outputs.get("lambda_function_name")
    assert function_name, "lambda_function_name output not found"


def test_ecs_runner_lambda_exists(lambda_client, ecs_runner_outputs):
    """Verify the ECS runner Lambda function exists."""
    function_name = ecs_runner_outputs.get("lambda_function_name")
    if not function_name:
        pytest.skip("lambda_function_name output not available")
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_ecs_runner_lambda_is_active(lambda_client, ecs_runner_outputs):
    """Verify the ECS runner Lambda function is active."""
    function_name = ecs_runner_outputs.get("lambda_function_name")
    if not function_name:
        pytest.skip("lambda_function_name output not available")
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["State"] == "Active"
