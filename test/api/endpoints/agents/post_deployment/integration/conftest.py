"""Pytest fixtures for agents post-deployment integration tests."""
from pathlib import Path

import boto3
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


@pytest.fixture(scope="session")
def agents_src_dir() -> Path:
    """Return the agents source directory."""
    return AGENTS_SRC


@pytest.fixture(scope="session")
def s3_prompts_bucket_name(shared_config):
    """Return the S3 bucket name for agent prompts."""
    return f"{shared_config['resource_prefix']}-agent-prompts"


@pytest.fixture(scope="session")
def s3_runtime_code_bucket_name(shared_config):
    """Return the S3 bucket name for agent runtime code."""
    return f"{shared_config['resource_prefix']}-agent-runtime-code"


@pytest.fixture(scope="session")
def bedrock_client(aws_region):
    """Create a Bedrock client."""
    return boto3.client("bedrock", region_name=aws_region)


@pytest.fixture(scope="session")
def bedrock_agentcore_client(aws_region):
    """Create a Bedrock AgentCore client."""
    return boto3.client("bedrock-agentcore", region_name=aws_region)


@pytest.fixture(scope="session")
def opensearch_client(aws_region):
    """Create an OpenSearch Serverless client."""
    return boto3.client("opensearchserverless", region_name=aws_region)


@pytest.fixture(scope="session")
def guardrail_name(shared_config):
    """Return the Bedrock guardrail name."""
    return f"{shared_config['resource_prefix']}-agent-guardrail"


@pytest.fixture(scope="session")
def memory_collection_name(shared_config):
    """Return the OpenSearch collection name for agent memory."""
    return f"{shared_config['resource_prefix']}-memory"


@pytest.fixture(scope="session")
def agentcore_runtime_name(shared_config):
    """Return the AgentCore runtime name."""
    return f"{shared_config['resource_prefix']}_agent_runtime".replace("-", "_")


@pytest.fixture(scope="session")
def sqs_client(aws_region):
    """Create an SQS client."""
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(scope="session")
def webhook_queue_name(shared_config):
    """Return the webhook FIFO queue name."""
    return f"{shared_config['resource_prefix']}-webhook-ingress.fifo"


@pytest.fixture(scope="session")
def webhook_dlq_name(shared_config):
    """Return the webhook DLQ FIFO queue name."""
    return f"{shared_config['resource_prefix']}-webhook-ingress-dlq.fifo"
