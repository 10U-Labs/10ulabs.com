"""Tests to validate ECS runner infrastructure exists for rack_designer endpoint."""


def test_ecs_runner_terraform_outputs_readable(ecs_runner_outputs):
    """Verify ecs_runner terraform outputs are accessible."""
    assert ecs_runner_outputs.get("cluster_arn"), \
        "cluster_arn output not found in ecs_runner"
    assert ecs_runner_outputs.get("cluster_name"), \
        "cluster_name output not found in ecs_runner"


def test_ecs_runner_lambda_exists(lambda_client, ecs_runner_outputs):
    """Verify the ECS runner Lambda function exists."""
    function_name = ecs_runner_outputs.get("lambda_function_name")
    assert function_name, "lambda_function_name output not found"

    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name
    assert response["Configuration"]["State"] == "Active"
