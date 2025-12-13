"""Pytest fixtures for pre-deployment integration tests.

These tests follow the 5-layer testing model from PRE_DEPLOYMENT_INTEGRATION_TESTS.md:
- Layer 1: Authentication - Are AWS credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: Existence - Do the required resources exist?
- Layer 4: Configuration - Are resources configured correctly?
- Layer 5: Capability - Can we perform required operations?

Inherited fixtures from parent conftest files:
- test/conftest.py: shared_config, aws_region, sts_client, iam_client,
  caller_identity, current_role_arn, current_role_name
- test/api/conftest.py: lambda_client, ecs_runner_terraform_initialized,
  ecs_runner_outputs, terraform_init, terraform_output
- test/api/endpoints/runners/conftest.py: dynamodb_client
"""
from test.api.conftest import REPO_ROOT, terraform_init, terraform_output
from terraform_config import get_runners_resource_names

import boto3
import pytest


EC2_RUNNER_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "ec2_runner"
RUNNERS_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "runners"


@pytest.fixture(scope="session")
def config(shared_config):
    """Provide config for integration tests.

    Shadows parent config fixture with simpler structure for integration tests.
    Resource names come from terraform_config (single source of truth).
    """
    prefix = shared_config.get('resource_prefix', 'TenULabs')
    resource_names = get_runners_resource_names(prefix)
    return {
        'resource_prefix': prefix,
        'aws_region': shared_config.get('aws_region', 'us-east-2'),
        'idempotency_table_name': resource_names['idempotency_table'],
        'circuit_breaker_state_table_name': resource_names['circuit_breaker_state_table'],
        'workflow_runners_table_name': resource_names['workflow_runners_table'],
        'incidents_table_name': resource_names['incidents_table'],
        'job_queue_name': resource_names['job_queue'],
        'job_dlq_name': resource_names['job_dlq'],
        'webhook_dlq_name': resource_names['webhook_dlq'],
        'drift_recovery_queue_name': resource_names['drift_recovery_queue'],
    }


# =============================================================================
# AWS Client Fixtures (only those not inherited from parents)
# =============================================================================

@pytest.fixture(scope="session")
def sqs_client(aws_region):
    """Create an SQS client."""
    return boto3.client("sqs", region_name=aws_region)


# =============================================================================
# Terraform Fixtures (only those not inherited from parents)
# =============================================================================

@pytest.fixture(scope="session")
def ec2_runner_terraform_initialized():
    """Initialize terraform for ec2_runner state access."""
    return terraform_init(EC2_RUNNER_DIR)


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
