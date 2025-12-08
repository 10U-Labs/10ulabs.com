"""Pytest fixtures for workflow_fixer agent integration tests."""

import boto3
import pytest


AWS_REGION = "us-east-2"
AGENT_RUNTIME_NAME = "TenULabs_workflow_fixer"
LAMBDA_NAME = "TenULabsWorkflowFixerWebhook"
ECR_REPO_NAME = "tenulabs-workflow-fixer-agent"
SSM_GITHUB_PAT = "/TenULabs/github_pat"


@pytest.fixture(scope="session")
def agentcore_control_client():
    """Create a Bedrock AgentCore Control Plane client for managing runtimes."""
    return boto3.client("bedrock-agentcore-control", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def agentcore_data_client():
    """Create a Bedrock AgentCore Data Plane client for invoking agents."""
    return boto3.client("bedrock-agentcore", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def lambda_client():
    """Create a Lambda client."""
    return boto3.client("lambda", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def ecr_client():
    """Create an ECR client."""
    return boto3.client("ecr", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def agent_runtime_name():
    """Provide the AgentCore runtime name."""
    return AGENT_RUNTIME_NAME


@pytest.fixture(scope="session")
def lambda_function_name():
    """Provide the Lambda function name."""
    return LAMBDA_NAME


@pytest.fixture(scope="session")
def ecr_repo_name():
    """Provide the ECR repository name."""
    return ECR_REPO_NAME


@pytest.fixture(scope="session")
def ssm_github_pat_name():
    """Provide the SSM parameter name for GitHub PAT."""
    return SSM_GITHUB_PAT


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
