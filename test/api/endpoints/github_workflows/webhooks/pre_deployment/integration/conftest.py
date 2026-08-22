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
- test/api/conftest.py: lambda_client, terraform_init, terraform_output
- test/api/endpoints/github_workflows/webhooks/conftest.py: dynamodb_client
"""
from test.api.conftest import REPO_ROOT, terraform_init, terraform_output
from terraform_config import get_webhooks_resource_names

import boto3
import pytest


API_BACKEND_DIR = REPO_ROOT / "src" / "api" / "common" / "routing"
RUNNERS_DIR = (
    REPO_ROOT / "src" / "api" / "endpoints" / "github_workflows" / "webhooks"
)


@pytest.fixture(scope="session")
def config(shared_config):
    """Provide config for integration tests.

    Shadows parent config fixture with simpler structure for integration tests.
    Resource names come from terraform_config (single source of truth).
    """
    prefix = shared_config['resource_prefix']
    resource_names = get_webhooks_resource_names(prefix)
    return {
        'resource_prefix': prefix,
        'aws_region': shared_config['aws_region'],
        'idempotency_table_name': resource_names['idempotency_table'],
        'circuit_open_state_table_name': resource_names['circuit_open_state_table'],
        'incidents_table_name': resource_names['incidents_table'],
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
def runners_terraform_initialized():
    """Initialize terraform for the webhooks stack state access."""
    return terraform_init(RUNNERS_DIR)


@pytest.fixture(scope="session")
def firehose_client(aws_region):
    """Create a Firehose client."""
    return boto3.client("firehose", region_name=aws_region)


@pytest.fixture(scope="session")
def firehose_delivery_stream_name(shared_config):
    """Get the Firehose delivery stream name for CloudWatch Logs.

    This is a prerequisite resource created by api_common_routing that the
    webhooks stack depends on for subscription filters.
    """
    prefix = shared_config.get('resource_prefix', 'TenULabs')
    return f"{prefix}-CloudWatchLogs"


@pytest.fixture(scope="session")
def cloudwatch_logs_firehose_role_name(shared_config):
    """Get the CloudWatch Logs Firehose role name.

    This is a prerequisite resource created by api_common_routing that the
    webhooks stack depends on for subscription filters.
    """
    prefix = shared_config.get('resource_prefix', 'TenULabs')
    return f"{prefix}CloudWatchLogsFirehose"


# =============================================================================
# API Shared Infrastructure Fixtures (REQUIRED - no defaults in data.tf)
# =============================================================================


# =============================================================================
# Shared Resource Fixtures (used by both L3 existence and L4 configuration)
# =============================================================================
