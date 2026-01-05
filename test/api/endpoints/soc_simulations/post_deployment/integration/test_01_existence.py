"""Layer 1: Existence tests for simulation-soc endpoint.

Verify that resources created by this deployment exist.
"""
from botocore.exceptions import ClientError


pytest_plugins = ['test_fixtures.aws']


def test_simulation_soc_handler_lambda_exists(lambda_client, shared_config):
    """Verify simulation-soc handler Lambda function exists."""
    function_name = shared_config.get("lambda_handler_names", {}).get(
        "simulation_soc", "TenULabsSimulationSocHandler"
    )
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        function_exists = response["Configuration"]["FunctionName"] == function_name
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            function_exists = False
        else:
            raise
    assert function_exists, f"Lambda function {function_name} does not exist"


def test_simulation_soc_handler_iam_role_exists(iam_client, shared_config):
    """Verify simulation-soc handler IAM role exists."""
    resource_prefix = shared_config.get("resource_prefix", "TenULabs")
    role_name = f"{resource_prefix}SimulationSocHandlerServiceRole"
    try:
        response = iam_client.get_role(RoleName=role_name)
        role_exists = response["Role"]["RoleName"] == role_name
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            role_exists = False
        else:
            raise
    assert role_exists, f"IAM role {role_name} does not exist"


def test_simulation_soc_handler_log_group_exists(handler_log_group):
    """Verify simulation-soc handler CloudWatch log group exists."""
    assert handler_log_group["exists"], (
        f"CloudWatch log group '{handler_log_group['name']}' does not exist"
    )


def test_simulation_soc_handler_basic_execution_policy_exists(iam_client, shared_config):
    """Verify basic execution policy attachment exists."""
    resource_prefix = shared_config.get("resource_prefix", "TenULabs")
    role_name = f"{resource_prefix}SimulationSocHandlerServiceRole"
    response = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
    has_basic_exec = any("AWSLambdaBasicExecutionRole" in arn for arn in policy_arns)
    assert has_basic_exec, f"Role {role_name} missing AWSLambdaBasicExecutionRole"


def test_simulation_soc_handler_kms_policy_exists(iam_client, shared_config):
    """Verify KMS inline policy exists on role."""
    resource_prefix = shared_config.get("resource_prefix", "TenULabs")
    role_name = f"{resource_prefix}SimulationSocHandlerServiceRole"
    response = iam_client.list_role_policies(RoleName=role_name)
    policy_names = response["PolicyNames"]
    has_kms_policy = any("kms" in name.lower() for name in policy_names)
    assert has_kms_policy, f"Role {role_name} missing KMS inline policy"


def test_simulation_soc_handler_lambda_permission_exists(lambda_client, shared_config):
    """Verify API Gateway invoke permission exists on Lambda."""
    function_name = shared_config.get("lambda_handler_names", {}).get(
        "simulation_soc", "TenULabsSimulationSocHandler"
    )
    try:
        response = lambda_client.get_policy(FunctionName=function_name)
        has_permission = "apigateway" in response["Policy"].lower()
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            has_permission = False
        else:
            raise
    assert has_permission, f"Lambda {function_name} missing API Gateway permission"
