"""Post-deployment configuration tests for drift_recoveries endpoint.

Layer 2: Verify all deployed resources are configured correctly.
These tests run after existence tests pass.
"""


# === Lambda Configuration ===


def test_lambda_runtime_is_python313(lambda_client, function_name):
    """Verify Lambda uses Python 3.13 runtime."""
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_lambda_architecture_is_arm64(lambda_client, function_name):
    """Verify Lambda uses arm64 architecture."""
    response = lambda_client.get_function(FunctionName=function_name)
    architectures = response["Configuration"].get("Architectures", [])
    assert "arm64" in architectures


def test_lambda_timeout_is_120_seconds(lambda_client, function_name):
    """Verify Lambda timeout is 120 seconds."""
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Timeout"] == 120


def test_lambda_memory_is_256mb(lambda_client, function_name):
    """Verify Lambda memory is 256 MB."""
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["MemorySize"] == 256


def test_lambda_has_github_repo_env_var(lambda_client, function_name):
    """Verify Lambda has GITHUB_REPO environment variable."""
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response["Configuration"].get("Environment", {}).get("Variables", {})
    assert "GITHUB_REPO" in env_vars


def test_lambda_has_github_token_parameter_name_env_var(lambda_client, function_name):
    """Verify Lambda has GITHUB_TOKEN_PARAMETER_NAME environment variable."""
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response["Configuration"].get("Environment", {}).get("Variables", {})
    assert "GITHUB_TOKEN_PARAMETER_NAME" in env_vars


def test_lambda_has_sns_topic_arn_env_var(lambda_client, function_name):
    """Verify Lambda has SNS_TOPIC_ARN environment variable."""
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response["Configuration"].get("Environment", {}).get("Variables", {})
    assert "SNS_TOPIC_ARN" in env_vars


def test_lambda_has_managed_vpc_id_env_var(lambda_client, function_name):
    """Verify Lambda has MANAGED_VPC_ID environment variable."""
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response["Configuration"].get("Environment", {}).get("Variables", {})
    assert "MANAGED_VPC_ID" in env_vars


# === CloudWatch Log Group Configuration ===


def test_lambda_log_group_has_30_day_retention(logs_client, function_name):
    """Verify Lambda log group has 30-day retention."""
    log_group_name = f"/aws/lambda/{function_name}"
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = response.get("logGroups", [])
    matching = next((lg for lg in log_groups if lg["logGroupName"] == log_group_name), None)
    assert matching.get("retentionInDays") == 30


# === EventBridge Configuration ===


def test_eventbridge_scheduled_rule_is_enabled(events_client, cfg):
    """Verify EventBridge scheduled rule is enabled."""
    rule_name = f"{cfg['resource_prefix']}-scheduled-check"
    response = events_client.describe_rule(Name=rule_name)
    assert response["State"] == "ENABLED"


def test_eventbridge_scheduled_rule_uses_rate_schedule(events_client, cfg):
    """Verify EventBridge scheduled rule uses rate-based schedule."""
    rule_name = f"{cfg['resource_prefix']}-scheduled-check"
    response = events_client.describe_rule(Name=rule_name)
    assert "rate(1 hour)" in response["ScheduleExpression"]
