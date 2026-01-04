"""Layer 5: Existence tests for runners endpoint pre-deployment validation.

Verify prerequisite resources exist (assumes authorization passed).
"""
import pytest
from botocore.exceptions import ClientError



class TestBootstrapPrerequisites:
    """Verify bootstrap prerequisites exist."""

    def test_state_bucket_exists(self, s3_client, state_bucket_name):
        """Verify the Terraform state bucket exists."""
        try:
            response = s3_client.head_bucket(Bucket=state_bucket_name)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                pytest.fail(
                    f"State bucket '{state_bucket_name}' does not exist. "
                    "Run terraform apply in src/bootstrap/"
                )
            raise

    def test_github_actions_role_exists(self, iam_client, github_actions_role_name):
        """Verify the GitHub Actions IAM role exists."""
        try:
            iam_client.get_role(RoleName=github_actions_role_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(
                    f"GitHub Actions role '{github_actions_role_name}' does not exist. "
                    "Run terraform apply in src/bootstrap/"
                )
            raise
        assert True  # Explicit pass


class TestAPICommonRoutingPrerequisites:
    """Verify API common routing prerequisites exist."""

    def test_api_gateway_exists(self, apigateway_client, api_gateway_id):
        """Verify the API Gateway REST API exists."""
        try:
            apigateway_client.get_rest_api(restApiId=api_gateway_id)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NotFoundException":
                pytest.fail(
                    f"API Gateway '{api_gateway_id}' does not exist. "
                    "Run terraform apply in src/api/common/routing/"
                )
            raise
        assert True  # Explicit pass

    def test_bootstrap_terraform_initialized(self, bootstrap_outputs):
        """Verify terraform init succeeds for bootstrap."""
        assert bootstrap_outputs, (
            "Terraform init failed for src/bootstrap/. "
            "Check AWS credentials and S3 backend configuration."
        )

    def test_api_common_routing_terraform_initialized(self, api_common_routing_outputs):
        """Verify terraform init succeeds for api_common_routing."""
        assert api_common_routing_outputs, (
            "Terraform init failed for src/api/common/routing/. "
            "Check AWS credentials and S3 backend configuration."
        )
