"""Pytest fixtures for agent_creator integration tests.

Shared fixtures (aws_region, ecr_repository_name, ecr_client, etc.) are
inherited from test/conftest.py which parses values from the shared
Terraform module.
"""

import boto3
import pytest


# Agent-specific constants
AGENT_RUNTIME_NAME = "TenULabs_agent_creator"
LAMBDA_NAME = "TenULabsAgentCreator"


@pytest.fixture(scope="session")
def agentcore_client(aws_region):
    """Create a Bedrock AgentCore client."""
    return boto3.client("bedrock-agentcore", region_name=aws_region)


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
