"""Pytest fixtures for test_auditor agent integration tests."""

import boto3
import pytest


AWS_REGION = "us-east-2"
AGENT_NAME = "TenULabsTestAuditorAgent"
LAMBDA_NAME = "TenULabsTestAuditorActionGroup"
ECR_REPO_NAME = "10ulabs/test_auditor-agent"


@pytest.fixture(scope="session")
def bedrock_agent_client():
    """Create a Bedrock Agent client for AgentCore."""
    return boto3.client("bedrock-agent", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def lambda_client():
    """Create a Lambda client."""
    return boto3.client("lambda", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def ecr_client():
    """Create an ECR client."""
    return boto3.client("ecr", region_name=AWS_REGION)


@pytest.fixture(scope="session")
def agent_name():
    """Provide the agent runtime name."""
    return AGENT_NAME


@pytest.fixture(scope="session")
def lambda_function_name():
    """Provide the Lambda function name."""
    return LAMBDA_NAME


@pytest.fixture(scope="session")
def ecr_repo_name():
    """Provide the ECR repository name."""
    return ECR_REPO_NAME
