"""Tests to validate ec2_runner infrastructure exists."""


def test_ec2_runner_terraform_outputs_readable(ec2_runner_outputs):
    """Verify ec2_runner terraform outputs are accessible."""
    assert ec2_runner_outputs.get("lambda_function_arn"), \
        "lambda_function_arn output not found in ec2_runner"
    assert ec2_runner_outputs.get("lambda_function_name"), \
        "lambda_function_name output not found in ec2_runner"
    assert ec2_runner_outputs.get("lambda_invoke_arn"), \
        "lambda_invoke_arn output not found in ec2_runner"


def test_ec2_runner_lambda_exists(lambda_client, ec2_runner_outputs):
    """Verify the EC2 runner Lambda function exists."""
    function_name = ec2_runner_outputs.get("lambda_function_name")
    assert function_name, "lambda_function_name output not found"

    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name
    assert response["Configuration"]["State"] == "Active"
