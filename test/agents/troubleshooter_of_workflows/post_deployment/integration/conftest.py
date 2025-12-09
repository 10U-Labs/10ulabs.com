"""Pytest fixtures for troubleshooter_of_workflows agent integration tests.

Shared fixtures (aws_region, ecr_repository_name, ecr_client, ssm_github_pat_name,
etc.) are inherited from test/conftest.py which parses values from the shared
Terraform module.
"""

import boto3
import pytest


# Agent-specific constants
AGENT_RUNTIME_NAME = "TenULabs_troubleshooter_of_workflows"
LAMBDA_NAME = "TenULabsTroubleshooterOfWorkflowsWebhook"


@pytest.fixture(scope="session")
def agentcore_control_client(aws_region):
    """Create a Bedrock AgentCore Control Plane client for managing runtimes."""
    return boto3.client("bedrock-agentcore-control", region_name=aws_region)


@pytest.fixture(scope="session")
def agentcore_data_client(aws_region):
    """Create a Bedrock AgentCore Data Plane client for invoking agents."""
    return boto3.client("bedrock-agentcore", region_name=aws_region)


@pytest.fixture(scope="session")
def lambda_client(aws_region):
    """Create a Lambda client."""
    return boto3.client("lambda", region_name=aws_region)


@pytest.fixture(scope="session")
def agent_runtime_name():
    """Provide the AgentCore runtime name."""
    return AGENT_RUNTIME_NAME


@pytest.fixture(scope="session")
def lambda_function_name():
    """Provide the Lambda function name."""
    return LAMBDA_NAME


@pytest.fixture(scope="session")
def ecr_repo_name(ecr_repository_name):
    """Alias for ecr_repository_name for backward compatibility."""
    return ecr_repository_name


@pytest.fixture(scope="session")
def webhook_url(lambda_client, lambda_function_name):
    """Get the Lambda function URL for the webhook."""
    try:
        response = lambda_client.get_function_url_config(
            FunctionName=lambda_function_name
        )
        return response.get("FunctionUrl")
    except lambda_client.exceptions.ResourceNotFoundException:
        return None


@pytest.fixture(scope="session")
def agent_runtime_arn(lambda_client, lambda_function_name):
    """Get the AgentCore runtime ARN from Lambda environment."""
    try:
        response = lambda_client.get_function(FunctionName=lambda_function_name)
        env_vars = response["Configuration"].get("Environment", {}).get(
            "Variables", {}
        )
        return env_vars.get("AGENT_RUNTIME_ARN")
    except lambda_client.exceptions.ResourceNotFoundException:
        return None
