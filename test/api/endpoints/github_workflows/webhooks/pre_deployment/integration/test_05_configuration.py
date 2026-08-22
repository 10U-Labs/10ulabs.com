"""Layer 5: Configuration - Are resources configured correctly?

These tests verify that resources are properly configured after confirming
they exist. Configuration checks include state, settings, and naming conventions.

Six-layer testing model:
- Layer 1: Authentication - Are credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: State - Does Terraform state match AWS reality?
- Layer 4: Existence - Do the required resources exist?
- Layer 5: Configuration - Are resources configured correctly? (THIS FILE)
- Layer 6: Capability - Can we perform required operations?
"""
from botocore.exceptions import ClientError
import pytest

from repo_utils import REPO_ROOT
from terraform_config import get_webhooks_resource_names


RUNNERS_SRC = (
    REPO_ROOT / "src" / "api" / "endpoints" / "github_workflows" / "webhooks"
)
SQS_TF_FILE = RUNNERS_SRC / "sqs.tf"


# =============================================================================
# Lambda Configuration
# =============================================================================


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
    """Layer 5: Verify SQS queue names follow expected conventions."""

    def test_webhook_dlq_uses_handler_prefix(self):
        """Verify webhook_dlq name uses the webhook handler name as prefix."""
        resource_names = get_webhooks_resource_names()
        webhook_dlq = resource_names['webhook_dlq']
        assert webhook_dlq.startswith('TenULabs'), (
            f"Queue {webhook_dlq} doesn't follow naming convention. "
            "Expected to start with resource prefix."
        )

    def test_dlq_names_include_dlq_suffix(self):
        """Verify DLQ names include 'Dlq' suffix."""
        resource_names = get_webhooks_resource_names()
        dlq_keys = [k for k in resource_names if 'dlq' in k]
        for key in dlq_keys:
            queue_name = resource_names[key]
            assert 'Dlq' in queue_name, (
                f"DLQ {key}={queue_name} doesn't include 'Dlq' suffix. "
                "DLQ names should clearly indicate dead letter queue purpose."
            )
