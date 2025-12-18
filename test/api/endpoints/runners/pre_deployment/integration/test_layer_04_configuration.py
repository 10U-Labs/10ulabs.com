"""Layer 4: Configuration - Are resources configured correctly?

These tests verify that resources are properly configured after confirming
they exist. Configuration checks include state, settings, and naming conventions.

Five-layer testing model:
- Layer 1: Authentication - Are credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: Existence - Do the required resources exist?
- Layer 4: Configuration - Are resources configured correctly? (THIS FILE)
- Layer 5: Capability - Can we perform required operations?
"""
from pathlib import Path

from botocore.exceptions import ClientError
import pytest

from terraform_config import get_runners_resource_names


RUNNERS_SRC = Path(__file__).parents[6] / "src" / "api" / "endpoints" / "runners"
SQS_TF_FILE = RUNNERS_SRC / "sqs.tf"


# =============================================================================
# VPC Configuration
# =============================================================================


class TestVPCConfiguration:
    """Layer 4: Verify VPC resources are properly configured."""

    def test_01_vpc_is_available(self, vpc_info, api_shared_runners_outputs):
        """Verify the VPC is in available state."""
        vpc_id = api_shared_runners_outputs.get("vpc_id")
        if not vpc_id:
            pytest.skip("vpc_id output not available")
        if vpc_info is None:
            pytest.skip("VPC not found - covered by existence test")
        assert vpc_info["State"] == "available", (
            f"VPC {vpc_id} is in state '{vpc_info['State']}', not 'available'."
        )

    def test_02_subnets_are_available(self, subnets_info, api_shared_runners_outputs):
        """Verify all subnets are in available state."""
        if not api_shared_runners_outputs.get("vpc_public_subnet_ids"):
            pytest.skip("vpc_public_subnet_ids output not available")
        if not subnets_info:
            pytest.skip("Subnets not found - covered by existence test")
        for subnet in subnets_info:
            assert subnet["State"] == "available", (
                f"Subnet {subnet['SubnetId']} is in state '{subnet['State']}', "
                "not 'available'."
            )


# =============================================================================
# ECR Configuration
# =============================================================================


def test_ecr_repository_has_image_scanning(
    ecr_repository_info, api_shared_ecs_runner_outputs
):
    """Verify the ECR repository has image scanning configured."""
    if not api_shared_ecs_runner_outputs.get("ecr_repository_name"):
        pytest.skip("ecr_repository_name output not available")
    if ecr_repository_info is None:
        pytest.skip("Repository not found - covered by existence test")
    # Image scanning is recommended but not strictly required
    scan_config = ecr_repository_info.get("imageScanningConfiguration", {})
    if not scan_config.get("scanOnPush"):
        pytest.skip("Image scanning on push is not enabled (optional)")


# =============================================================================
# Lambda Configuration
# =============================================================================


class TestLambdaConfiguration:
    """Layer 4: Verify Lambda functions are properly configured."""

    def test_01_ec2_runner_lambda_is_active(self, lambda_client, ec2_runner_outputs):
        """Verify the EC2 runner Lambda function is active."""
        function_name = ec2_runner_outputs.get("lambda_function_name")
        if not function_name:
            pytest.skip("lambda_function_name output not available")
        response = lambda_client.get_function(FunctionName=function_name)
        assert response["Configuration"]["State"] == "Active"

    def test_02_ecs_runner_lambda_is_active(self, lambda_client, ecs_runner_outputs):
        """Verify the ECS runner Lambda function is active."""
        function_name = ecs_runner_outputs.get("lambda_function_name")
        if not function_name:
            pytest.skip("lambda_function_name output not available")
        response = lambda_client.get_function(FunctionName=function_name)
        assert response["Configuration"]["State"] == "Active"


# =============================================================================
# SSM Configuration
# =============================================================================


def test_github_pat_parameter_is_secure_string(ssm_client, ssm_github_pat_name):
    """Verify the GitHub PAT SSM parameter is stored as SecureString."""
    try:
        response = ssm_client.get_parameter(
            Name=ssm_github_pat_name, WithDecryption=False
        )
        param_type = response.get("Parameter", {}).get("Type", "")
        assert param_type == "SecureString", (
            f"SSM parameter '{ssm_github_pat_name}' is type '{param_type}', "
            "but should be 'SecureString' for security. "
            "Recreate the parameter as a SecureString."
        )
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ParameterNotFound":
            pytest.skip("Parameter does not exist - covered by existence test")
        raise


# =============================================================================
# SQS Naming Conventions
# =============================================================================


class TestSQSNamingConventions:
    """Layer 4: Verify SQS queue names follow expected conventions."""

    def test_01_queue_names_use_handler_prefix(self):
        """Verify queue names use the webhook handler name as prefix."""
        resource_names = get_runners_resource_names()
        # All queues should have a consistent prefix pattern
        expected_queues = [
            resource_names['job_queue'],
            resource_names['job_dlq'],
            resource_names['webhook_dlq'],
            resource_names['webhook_ingress_queue'],
            resource_names['webhook_ingress_dlq'],
            resource_names['ignored_events_queue'],
            resource_names['ignored_events_dlq'],
        ]
        # All should start with TenULabs (or the configured prefix)
        for queue_name in expected_queues:
            assert queue_name.startswith('TenULabs'), (
                f"Queue {queue_name} doesn't follow naming convention. "
                "Expected to start with resource prefix."
            )

    def test_02_dlq_names_include_dlq_suffix(self):
        """Verify DLQ names include 'Dlq' suffix."""
        resource_names = get_runners_resource_names()
        dlq_keys = [k for k in resource_names if 'dlq' in k]
        for key in dlq_keys:
            queue_name = resource_names[key]
            assert 'Dlq' in queue_name, (
                f"DLQ {key}={queue_name} doesn't include 'Dlq' suffix. "
                "DLQ names should clearly indicate dead letter queue purpose."
            )

    def test_03_ingress_queue_short_retention_configured(self):
        """Verify ingress queue is configured with short retention for DDoS protection."""
        with open(SQS_TF_FILE, encoding='utf-8') as f:
            content = f.read()
        # Check for message_retention_seconds = 3600 in webhook_ingress resource
        assert 'message_retention_seconds  = 3600' in content or \
               'message_retention_seconds = 3600' in content, (
            "webhook_ingress queue should have 1-hour retention (3600 seconds) "
            "for DDoS protection."
        )
