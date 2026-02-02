"""Post-deployment configuration tests for github_workflows/retries endpoint.

Layer 2: Verify all deployed resources are configured correctly.
These tests run after existence tests pass.
"""
import re


# === Lambda Function Configuration ===


def test_lambda_uses_python_313_runtime(lambda_client, config):
    """Verify Lambda uses Python 3.13 runtime."""
    function_name = config["function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_lambda_uses_arm64_architecture(lambda_client, config):
    """Verify Lambda uses ARM64 architecture."""
    function_name = config["function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert "arm64" in response["Configuration"]["Architectures"]


def test_lambda_has_60_second_timeout(lambda_client, config):
    """Verify Lambda has 60 second timeout."""
    function_name = config["function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Timeout"] == 60


def test_lambda_has_256_mb_memory(lambda_client, config):
    """Verify Lambda has 256 MB memory."""
    function_name = config["function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["MemorySize"] == 256


def test_lambda_has_github_token_env_var(lambda_client, config):
    """Verify Lambda has GITHUB_TOKEN_SECRET_NAME environment variable."""
    function_name = config["function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response["Configuration"].get("Environment", {}).get("Variables", {})
    assert "GITHUB_TOKEN_SECRET_NAME" in env_vars


# === CloudWatch Log Group Configuration ===


def test_handler_log_group_has_retention(handler_log_group):
    """Verify handler log group has retention configured."""
    assert handler_log_group["retention"] is not None, (
        f"Log group '{handler_log_group['name']}' has no retention policy"
    )


def test_handler_log_group_retention_is_7_days(handler_log_group):
    """Verify handler log group retention is 7 days."""
    retention = handler_log_group["retention"]
    assert retention == 7, (
        f"Log group '{handler_log_group['name']}' "
        f"retention is {retention} days, expected 7"
    )


# === Resource Naming Conventions ===


def _is_pascalcase(name):
    """Check if name follows PascalCase convention (no dashes, underscores)."""
    return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))


def test_handler_function_name_is_pascalcase(lambda_client, config):
    """Verify handler function uses PascalCase naming."""
    function_name = config["function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    actual_name = response["Configuration"]["FunctionName"]
    assert _is_pascalcase(actual_name), f"Name '{actual_name}' is not PascalCase"
