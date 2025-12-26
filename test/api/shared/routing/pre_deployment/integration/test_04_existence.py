"""Layer 4: Existence tests for api_shared_routing pre-deployment validation.

Verify prerequisite resources exist (assumes authorization passed).
"""
import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import (
    Layer4IAMRoleExistenceTests,
    Layer4TerraformStateExistenceTests,
)

pytestmark = pytest.mark.layer(4)


class TestIAMAndStateExistence(
    Layer4IAMRoleExistenceTests, Layer4TerraformStateExistenceTests
):
    """Layer 4: Verify IAM role and state bucket exist.

    All tests inherited from base classes.
    """


class TestBootstrapPrerequisites:
    """Layer 4: Verify bootstrap prerequisites exist."""

    def test_bootstrap_terraform_initialized(self, bootstrap_initialized):
        """Verify terraform init succeeds for bootstrap."""
        assert bootstrap_initialized, (
            "Terraform init failed for src/bootstrap/. "
            "Check AWS credentials and S3 backend configuration."
        )

    def test_central_logs_bucket_arn_output_exists(self, bootstrap_outputs):
        """Verify arn_for_central_logs_bucket output exists."""
        arn = bootstrap_outputs.get("arn_for_central_logs_bucket")
        assert arn, (
            "arn_for_central_logs_bucket output not found in bootstrap. "
            "Check src/bootstrap/outputs.tf"
        )

    def test_github_actions_role_arn_output_exists(self, bootstrap_outputs):
        """Verify arn_for_github_actions_role output exists."""
        arn = bootstrap_outputs.get("arn_for_github_actions_role")
        assert arn, (
            "arn_for_github_actions_role output not found in bootstrap. "
            "Check src/bootstrap/outputs.tf"
        )

    def test_central_logs_bucket_name_extracted(self, central_logs_bucket_name):
        """Verify central logs bucket name was extracted from ARN."""
        assert central_logs_bucket_name, (
            "Could not extract bucket name from arn_for_central_logs_bucket. "
            "Check bootstrap outputs."
        )

    def test_central_logs_bucket_exists(self, s3_client, central_logs_bucket_name):
        """Verify the central logs bucket exists."""
        if not central_logs_bucket_name:
            pytest.skip("central_logs_bucket_name not available")
        try:
            response = s3_client.head_bucket(Bucket=central_logs_bucket_name)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                pytest.fail(
                    f"Central logs bucket '{central_logs_bucket_name}' does not exist. "
                    "Run terraform apply in src/bootstrap/"
                )
            raise
