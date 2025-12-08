"""Pytest fixtures for workflow_fixer agent integration tests."""

import boto3
import pytest


AWS_REGION = "us-east-2"
AGENT_RUNTIME_NAME = "TenULabs_workflow_fixer"
LAMBDA_NAME = "TenULabsWorkflowFixerWebhook"
ECR_REPO_NAME = "tenulabs-workflow-fixer-agent"


@pytest.fixture(scope="session")
def agentcore_client():
    """Create a Bedrock AgentCore client."""
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
