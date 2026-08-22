"""Layer 4: Existence - Do the required resources exist?

These tests verify that all required infrastructure resources exist before
checking their configuration. Organized by resource type for clarity.

Six-layer testing model:
- Layer 1: Authentication - Are credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: State - Does Terraform state match AWS reality?
- Layer 4: Existence - Do the required resources exist? (THIS FILE)
- Layer 5: Configuration - Are resources configured correctly?
- Layer 6: Capability - Can we perform required operations?
"""
from botocore.exceptions import ClientError
import pytest

from repo_utils import REPO_ROOT
from terraform_config import extract_sqs_queue_names


RUNNERS_SRC = (
    REPO_ROOT / "src" / "api" / "endpoints" / "github_workflows" / "webhooks"
)
SQS_TF_FILE = RUNNERS_SRC / "sqs.tf"


# =============================================================================
# Terraform Outputs Existence
# =============================================================================


class TestApiBackendFirehoseResources:
    """Layer 4: Verify api_common_routing Firehose resources exist in AWS."""

    def test_firehose_delivery_stream_exists(
        self, firehose_client, firehose_delivery_stream_name
    ):
        """Verify Firehose delivery stream exists.

        This resource is created by api_common_routing and required for the webhooks stack
        subscription filters to route logs to S3.
        """
        response = firehose_client.describe_delivery_stream(
            DeliveryStreamName=firehose_delivery_stream_name
        )
        assert response["DeliveryStreamDescription"]["DeliveryStreamName"] == (
            firehose_delivery_stream_name
        ), (
            f"Firehose delivery stream '{firehose_delivery_stream_name}' not found. "
            "Run: cd src/api/common/routing && terraform apply"
        )

    def test_cloudwatch_logs_firehose_role_exists(
        self, iam_client, cloudwatch_logs_firehose_role_name
    ):
        """Verify CloudWatch Logs Firehose IAM role exists.

        This role is created by api_common_routing and required for subscription
        filters to write to Firehose.
        """
        response = iam_client.get_role(RoleName=cloudwatch_logs_firehose_role_name)
        assert response["Role"]["RoleName"] == cloudwatch_logs_firehose_role_name, (
            f"IAM role '{cloudwatch_logs_firehose_role_name}' not found. "
            "Run: cd src/api/common/routing && terraform apply"
        )


# =============================================================================
# AWS Resource Existence
# =============================================================================


class TestSSMResourceExistence:
    """Layer 4: Verify SSM parameters exist in AWS."""

    def test_github_pat_parameter_exists(self, ssm_client, ssm_github_pat_name):
        """Verify the GitHub PAT SSM parameter exists."""
        try:
            response = ssm_client.get_parameter(
                Name=ssm_github_pat_name, WithDecryption=False
            )
            assert response.get("Parameter") is not None, (
                f"SSM parameter '{ssm_github_pat_name}' returned empty response."
            )
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "ParameterNotFound":
                pytest.fail(
                    f"SSM parameter '{ssm_github_pat_name}' does not exist. "
                    "This parameter must be created manually with a valid GitHub PAT."
                )
            raise

    def test_github_pat_parameter_has_value(self, ssm_client, ssm_github_pat_name):
        """Verify the GitHub PAT SSM parameter has a non-empty value."""
        try:
            response = ssm_client.get_parameter(
                Name=ssm_github_pat_name, WithDecryption=True
            )
            value = response.get("Parameter", {}).get("Value", "")
            assert value, (
                f"SSM parameter '{ssm_github_pat_name}' exists but has empty value. "
                "Update the parameter with a valid GitHub PAT."
            )
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "ParameterNotFound":
                pytest.skip("Parameter does not exist - covered by existence test")
            if code == "AccessDeniedException":
                pytest.skip("No permission to decrypt - checking existence only")
            raise


# =============================================================================
# Terraform Configuration Existence (pre-deployment validation)
# =============================================================================


class TestSQSTerraformConfigExistence:
    """Layer 4: Verify SQS queue definitions exist in Terraform config."""

    def test_sqs_tf_file_exists(self):
        """Verify sqs.tf file exists in the webhooks endpoint."""
        assert SQS_TF_FILE.exists(), (
            f"sqs.tf not found at {SQS_TF_FILE}. "
            "The webhooks endpoint requires SQS queue definitions."
        )

    def test_sqs_queues_extractable(self):
        """Verify SQS queue names can be extracted from sqs.tf."""
        queues = extract_sqs_queue_names(SQS_TF_FILE)
        assert len(queues) > 0, (
            "No SQS queue definitions found in sqs.tf. "
            "Expected at least one aws_sqs_queue resource."
        )

    def test_webhook_dlq_defined(self):
        """Verify webhook_dlq is defined in Terraform."""
        queues = extract_sqs_queue_names(SQS_TF_FILE)
        queue_resources = [name for name, _ in queues]
        assert "webhook_dlq" in queue_resources, (
            "webhook_dlq not found in sqs.tf. "
            "Required for failed webhook message handling."
        )
