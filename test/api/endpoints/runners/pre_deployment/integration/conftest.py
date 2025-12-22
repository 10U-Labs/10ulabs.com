"""Pytest fixtures for pre-deployment integration tests.

These tests follow the 6-layer testing model from PRE_DEPLOYMENT_INTEGRATION_TESTS.md:
- Layer 1: Authentication - Are AWS credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: State - Does Terraform state match AWS reality?
- Layer 4: Existence - Do the required resources exist?
- Layer 5: Configuration - Are resources configured correctly?
- Layer 6: Capability - Can we perform required operations?

Inherited fixtures from parent conftest files:
- test/conftest.py: shared_config, aws_region, sts_client, iam_client,
  caller_identity, current_role_arn, current_role_name, ssm_client, ssm_github_pat_name
- test/api/conftest.py: lambda_client, ecs_runner_terraform_initialized,
  ecs_runner_outputs, terraform_init, terraform_output
- test/api/endpoints/runners/conftest.py: dynamodb_client
"""
from test.api.conftest import REPO_ROOT, terraform_init, terraform_output
from terraform_config import get_runners_resource_names

import boto3
import pytest

# Enable layer marker plugin for test ordering
pytest_plugins = ['pytest_layers']


API_SHARED_ECS_RUNNER_DIR = REPO_ROOT / "src" / "api" / "shared" / "ecs_runner"
API_SHARED_RUNNERS_DIR = REPO_ROOT / "src" / "api" / "shared" / "runners"
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
        # New queues for API Gateway → SQS direct integration
        'webhook_ingress_queue_name': resource_names['webhook_ingress_queue'],
        'webhook_ingress_dlq_name': resource_names['webhook_ingress_dlq'],
        'ignored_events_queue_name': resource_names['ignored_events_queue'],
        'ignored_events_dlq_name': resource_names['ignored_events_dlq'],
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


# =============================================================================
# API Shared Infrastructure Fixtures (REQUIRED - no defaults in data.tf)
# =============================================================================

@pytest.fixture(scope="session")
def ec2_client(aws_region):
    """Create an EC2 client."""
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(scope="session")
def api_shared_runners_terraform_initialized():
    """Initialize terraform for api_shared_runners state access."""
    return terraform_init(API_SHARED_RUNNERS_DIR)


@pytest.fixture(scope="session")
def api_shared_runners_outputs(request):
    """Get api_shared_runners terraform outputs.

    These outputs are REQUIRED (no defaults in runners/data.tf):
    - vpc_id: Used by drift_recovery Lambda and outputs passthrough
    - vpc_public_subnet_ids: Used by outputs passthrough
    - runner_security_group_id: Used by outputs passthrough
    """
    if not request.getfixturevalue("api_shared_runners_terraform_initialized"):
        pytest.skip("Terraform init failed for api_shared_runners")
    return {
        "vpc_id": terraform_output(API_SHARED_RUNNERS_DIR, "vpc_id"),
        "vpc_public_subnet_ids": terraform_output(
            API_SHARED_RUNNERS_DIR, "vpc_public_subnet_ids"
        ),
        "runner_security_group_id": terraform_output(
            API_SHARED_RUNNERS_DIR, "runner_security_group_id"
        ),
    }


@pytest.fixture(scope="session")
def api_shared_ecs_runner_terraform_initialized():
    """Initialize terraform for api_shared_ecs_runner state access."""
    return terraform_init(API_SHARED_ECS_RUNNER_DIR)


@pytest.fixture(scope="session")
def api_shared_ecs_runner_outputs(request):
    """Get api_shared_ecs_runner terraform outputs.

    These outputs are REQUIRED (no defaults in runners/data.tf):
    - ecr_repository_arn: Used by outputs passthrough
    - ecr_repository_name: Used by outputs passthrough
    - ecr_repository_url: Used by outputs passthrough
    """
    if not request.getfixturevalue("api_shared_ecs_runner_terraform_initialized"):
        pytest.skip("Terraform init failed for api_shared_ecs_runner")
    return {
        "ecr_repository_arn": terraform_output(
            API_SHARED_ECS_RUNNER_DIR, "ecr_repository_arn"
        ),
        "ecr_repository_name": terraform_output(
            API_SHARED_ECS_RUNNER_DIR, "ecr_repository_name"
        ),
        "ecr_repository_url": terraform_output(
            API_SHARED_ECS_RUNNER_DIR, "ecr_repository_url"
        ),
    }


# =============================================================================
# Shared Resource Fixtures (used by both L3 existence and L4 configuration)
# =============================================================================

@pytest.fixture(scope="session")
def vpc_info(request):
    """Fetch VPC details from AWS. Returns None if VPC not found."""
    client = request.getfixturevalue("ec2_client")
    outputs = request.getfixturevalue("api_shared_runners_outputs")
    vpc_id = outputs.get("vpc_id")
    if not vpc_id:
        return None
    try:
        response = client.describe_vpcs(VpcIds=[vpc_id])
        return response["Vpcs"][0] if response["Vpcs"] else None
    except client.exceptions.ClientError:
        return None


@pytest.fixture(scope="session")
def subnets_info(request):
    """Fetch subnet details from AWS. Returns empty list if not found."""
    client = request.getfixturevalue("ec2_client")
    outputs = request.getfixturevalue("api_shared_runners_outputs")
    subnet_ids_str = outputs.get("vpc_public_subnet_ids")
    if not subnet_ids_str:
        return []
    subnet_ids = [s.strip() for s in subnet_ids_str.split(",") if s.strip()]
    try:
        response = client.describe_subnets(SubnetIds=subnet_ids)
        return response["Subnets"]
    except client.exceptions.ClientError:
        return []


@pytest.fixture(scope="session")
def ecr_repository_info(request):
    """Fetch ECR repository details from AWS. Returns None if not found."""
    client = request.getfixturevalue("ecr_client")
    outputs = request.getfixturevalue("api_shared_ecs_runner_outputs")
    repo_name = outputs.get("ecr_repository_name")
    if not repo_name:
        return None
    try:
        response = client.describe_repositories(repositoryNames=[repo_name])
        return response["repositories"][0] if response["repositories"] else None
    except client.exceptions.ClientError:
        return None
