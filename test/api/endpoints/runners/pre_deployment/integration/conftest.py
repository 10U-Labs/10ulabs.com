"""Pytest fixtures for pre-deployment integration tests.

These tests follow the 5-layer testing model from PRE_DEPLOYMENT_INTEGRATION_TESTS.md:
- Layer 1: Authentication - Are AWS credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: Existence - Do the required resources exist?
- Layer 4: Configuration - Are resources configured correctly?
- Layer 5: Capability - Can we perform required operations?

Common fixtures (shared_config, aws_region, ecs_runner_outputs,
ecs_runner_terraform_initialized) are inherited from parent conftest files.
"""
from test.api.conftest import REPO_ROOT, terraform_init, terraform_output

import boto3
import pytest


EC2_RUNNER_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "ec2_runner"
ECS_RUNNER_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "ecs_runner"
RUNNERS_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "runners"


@pytest.fixture(scope="session")
def config(shared_config):
    """Provide config for integration tests.

    Shadows parent config fixture with simpler structure for integration tests.
    """
    prefix = shared_config.get('resource_prefix', 'TenULabs')
    return {
        'resource_prefix': prefix,
        'aws_region': shared_config.get('aws_region', 'us-east-2'),
        'idempotency_table_name': f"{prefix}-idempotency",
        'circuit_breaker_state_table_name': f"{prefix}-circuit-breaker-state",
        'workflow_runners_table_name': f"{prefix}-workflow-runners",
        'incidents_table_name': f"{prefix}-incidents",
        'job_queue_name': f"{prefix}-jobs",
        'job_dlq_name': f"{prefix}-job-dlq",
        'webhook_dlq_name': f"{prefix}-dlq",
        'drift_recovery_queue_name': f"{prefix}-DriftRecovery.fifo",
    }


# =============================================================================
# AWS Client Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def sts_client(aws_region):
    """Create an STS client for authentication tests."""
    return boto3.client("sts", region_name=aws_region)


@pytest.fixture(scope="session")
def iam_client(aws_region):
    """Create an IAM client for authorization tests."""
    return boto3.client("iam", region_name=aws_region)


@pytest.fixture(scope="session")
def sqs_client(aws_region):
    """Create an SQS client."""
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(scope="session")
def dynamodb_client(aws_region):
    """Create a session-scoped DynamoDB client for integration tests."""
    return boto3.client("dynamodb", region_name=aws_region)


# =============================================================================
# Identity Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def caller_identity(request):
    """Get the current caller identity."""
    client = request.getfixturevalue("sts_client")
    return client.get_caller_identity()


@pytest.fixture(scope="session")
def current_role_arn(request):
    """Extract the role ARN from caller identity."""
    identity = request.getfixturevalue("caller_identity")
    arn = identity.get("Arn", "")
    if ":assumed-role/" in arn:
        account = identity.get("Account", "")
        role_name = arn.split("/")[1]
        return f"arn:aws:iam::{account}:role/{role_name}"
    return arn


@pytest.fixture(scope="session")
def current_role_name(request):
    """Extract the role name from the role ARN."""
    role_arn = request.getfixturevalue("current_role_arn")
    if not role_arn:
        return ""
    return role_arn.split("/")[-1]


# =============================================================================
# Terraform Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def ec2_runner_terraform_initialized():
    """Initialize terraform for ec2_runner state access."""
    return terraform_init(EC2_RUNNER_DIR)


@pytest.fixture(scope="session")
def ecs_runner_terraform_initialized():
    """Initialize terraform for ecs_runner state access."""
    return terraform_init(ECS_RUNNER_DIR)


@pytest.fixture(scope="session")
def runners_terraform_initialized():
    """Initialize terraform for runners state access."""
    return terraform_init(RUNNERS_DIR)


@pytest.fixture(scope="session")
def ec2_runner_outputs(request):
    """Get ec2_runner terraform outputs."""
    if not request.getfixturevalue("ec2_runner_terraform_initialized"):
        pytest.skip("Terraform init failed for ec2_runner")
    return {
        "lambda_function_arn": terraform_output(
            EC2_RUNNER_DIR, "lambda_function_arn"
        ),
        "lambda_function_name": terraform_output(
            EC2_RUNNER_DIR, "lambda_function_name"
        ),
        "lambda_invoke_arn": terraform_output(
            EC2_RUNNER_DIR, "lambda_invoke_arn"
        ),
        "ec2_instance_profile_name": terraform_output(
            EC2_RUNNER_DIR, "ec2_instance_profile_name"
        ),
        "ec2_runner_role_arn": terraform_output(
            EC2_RUNNER_DIR, "ec2_runner_role_arn"
        ),
    }


@pytest.fixture(scope="session")
def ecs_runner_outputs(request):
    """Get ecs_runner terraform outputs."""
    if not request.getfixturevalue("ecs_runner_terraform_initialized"):
        pytest.skip("Terraform init failed for ecs_runner")
    return {
        "lambda_function_arn": terraform_output(
            ECS_RUNNER_DIR, "lambda_function_arn"
        ),
        "lambda_function_name": terraform_output(
            ECS_RUNNER_DIR, "lambda_function_name"
        ),
        "cluster_arn": terraform_output(ECS_RUNNER_DIR, "cluster_arn"),
        "cluster_name": terraform_output(ECS_RUNNER_DIR, "cluster_name"),
    }
