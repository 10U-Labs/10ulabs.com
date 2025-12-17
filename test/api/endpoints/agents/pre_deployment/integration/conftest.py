"""Pytest fixtures for agents pre-deployment integration tests.

These tests follow the 5-layer testing model from PRE_DEPLOYMENT_INTEGRATION_TESTS.md:
- Layer 1: Authentication - Are AWS credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: Existence - Do the required resources exist?
- Layer 4: Configuration - Are resources configured correctly?
- Layer 5: Capability - Can we perform required operations?

Inherited fixtures from parent conftest files:
- test/conftest.py: shared_config, aws_region, sts_client, iam_client, ssm_client,
  kms_client, ecr_client, caller_identity, current_role_arn, current_role_name,
  ecr_repository_name
"""
from pathlib import Path

import boto3
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


@pytest.fixture(scope="module")
def agents_src_dir() -> Path:
    """Return the agents source directory."""
    return AGENTS_SRC


# =============================================================================
# GitHub App SSM Parameter Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def github_app_ssm_prefix():
    """Return the GitHub App SSM parameter prefix."""
    return "/github/app"


@pytest.fixture(scope="session")
def github_app_ssm_id_name(github_app_ssm_prefix):
    """Return the GitHub App ID SSM parameter name."""
    return f"{github_app_ssm_prefix}/id"


@pytest.fixture(scope="session")
def github_app_ssm_installation_id_name(github_app_ssm_prefix):
    """Return the GitHub App Installation ID SSM parameter name."""
    return f"{github_app_ssm_prefix}/installation_id"


@pytest.fixture(scope="session")
def github_app_ssm_private_key_name(github_app_ssm_prefix):
    """Return the GitHub App Private Key SSM parameter name."""
    return f"{github_app_ssm_prefix}/private_key"


# =============================================================================
# KMS Key Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def kms_lambda_key_alias():
    """Return the KMS key alias used for Lambda environment variables."""
    return "alias/aws/lambda"


@pytest.fixture(scope="session")
def bedrock_client(aws_region):
    """Create a Bedrock client."""
    return boto3.client("bedrock", region_name=aws_region)


@pytest.fixture(scope="session")
def s3_prompts_bucket_name(shared_config):
    """Return the S3 bucket name for agent prompts."""
    return f"{shared_config['resource_prefix']}-agent-prompts"


@pytest.fixture(scope="session")
def s3_runtime_code_bucket_name(shared_config):
    """Return the S3 bucket name for agent runtime code."""
    return f"{shared_config['resource_prefix']}-agent-runtime-code"


@pytest.fixture(scope="session")
def opensearch_client(aws_region):
    """Create an OpenSearch Serverless client."""
    return boto3.client("opensearchserverless", region_name=aws_region)


@pytest.fixture(scope="session")
def memory_collection_name(shared_config):
    """Return the OpenSearch collection name for agent memory."""
    return f"{shared_config['resource_prefix']}-memory"


# =============================================================================
# API Gateway Fixtures (for FIFO queue integration tests)
# =============================================================================

@pytest.fixture(scope="session")
def apigateway_client(aws_region):
    """Create an API Gateway client."""
    return boto3.client("apigateway", region_name=aws_region)


@pytest.fixture(scope="session")
def sqs_client(aws_region):
    """Create an SQS client."""
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(scope="session")
def api_gateway_id(shared_config):
    """Return the API Gateway REST API ID."""
    return shared_config.get("api_gateway_id")


@pytest.fixture(scope="session")
def webhook_queue_name(shared_config):
    """Return the webhook FIFO queue name."""
    return f"{shared_config['resource_prefix']}-webhook-ingress.fifo"
