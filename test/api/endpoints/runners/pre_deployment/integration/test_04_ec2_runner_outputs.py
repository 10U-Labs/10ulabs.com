"""Tests to validate ec2_runner infrastructure exists."""
import pytest


def test_ec2_runner_has_lambda_function_arn_output(ec2_runner_outputs):
    """Verify ec2_runner has lambda_function_arn output."""
    assert ec2_runner_outputs.get("lambda_function_arn"), \
        "lambda_function_arn output not found in ec2_runner"


def test_ec2_runner_has_lambda_function_name_output(ec2_runner_outputs):
    """Verify ec2_runner has lambda_function_name output."""
    assert ec2_runner_outputs.get("lambda_function_name"), \
        "lambda_function_name output not found in ec2_runner"


def test_ec2_runner_has_lambda_invoke_arn_output(ec2_runner_outputs):
    """Verify ec2_runner has lambda_invoke_arn output."""
    assert ec2_runner_outputs.get("lambda_invoke_arn"), \
        "lambda_invoke_arn output not found in ec2_runner"


def test_ec2_runner_lambda_function_name_available(ec2_runner_outputs):
    """Verify lambda_function_name output is available for lookup."""
    function_name = ec2_runner_outputs.get("lambda_function_name")
    assert function_name, "lambda_function_name output not found"


def test_ec2_runner_lambda_exists(lambda_client, ec2_runner_outputs):
    """Verify the EC2 runner Lambda function exists."""
    function_name = ec2_runner_outputs.get("lambda_function_name")
    if not function_name:
        pytest.skip("lambda_function_name output not available")
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_ec2_runner_lambda_is_active(lambda_client, ec2_runner_outputs):
    """Verify the EC2 runner Lambda function is active."""
    function_name = ec2_runner_outputs.get("lambda_function_name")
    if not function_name:
        pytest.skip("lambda_function_name output not available")
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["State"] == "Active"
