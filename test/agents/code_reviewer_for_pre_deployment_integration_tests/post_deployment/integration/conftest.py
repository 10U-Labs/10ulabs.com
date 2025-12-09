"""Pytest fixtures for test_auditor agent integration tests.

Shared fixtures (aws_region, ecr_repository_name, ecr_client, etc.) are
inherited from test/conftest.py which parses values from the shared
Terraform module.
"""

import boto3
import pytest


# Agent-specific constants
AGENT_NAME = "TenULabsTestAuditorAgent"
LAMBDA_NAME = "TenULabsTestAuditorActionGroup"


@pytest.fixture(scope="session")
def bedrock_agent_client(aws_region):
    """Create a Bedrock Agent client for AgentCore."""
    return boto3.client("bedrock-agent", region_name=aws_region)


@pytest.fixture(scope="session")
def lambda_client(aws_region):
    """Create a Lambda client."""
    return boto3.client("lambda", region_name=aws_region)


@pytest.fixture(scope="session")
def agent_name():
    """Provide the agent runtime name."""
    return AGENT_NAME


@pytest.fixture(scope="session")
def lambda_function_name():
    """Provide the Lambda function name."""
    return LAMBDA_NAME


@pytest.fixture(scope="session")
def ecr_repo_name(ecr_repository_name):
    """Alias for ecr_repository_name for backward compatibility."""
    return ecr_repository_name
