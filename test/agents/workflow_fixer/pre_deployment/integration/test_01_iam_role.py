"""Tests to validate IAM role and credentials before workflow_fixer deployment.

These tests MUST run first (test_01_) because all other tests depend on having
valid AWS credentials and IAM permissions.

Five-layer testing model:
- Layer 1: Authentication - Are credentials configured and valid?
- Layer 2: Authorization - Can we call required APIs?
- Layer 3: Existence - Does the role exist?
- Layer 4: Configuration - Does the role have required policies?
"""

from botocore.exceptions import ClientError, NoCredentialsError
import pytest


class TestAWSCredentialsExistence:
    """Layer 1: Verify AWS credentials are available and valid."""

    def test_01_credentials_available(self, sts_client):
        """Verify AWS credentials are configured."""
        try:
            sts_client.get_caller_identity()
        except NoCredentialsError:
            pytest.fail(
                "No AWS credentials found. "
                "Configure credentials via environment variables, "
                "~/.aws/credentials, or IAM role."
            )

    def test_02_can_call_sts_api(self, sts_client):
        """Verify we can call sts:GetCallerIdentity."""
        try:
            response = sts_client.get_caller_identity()
            assert "Account" in response
            assert "Arn" in response
        except ClientError as err:
            pytest.fail(
                f"Failed to call sts:GetCallerIdentity: {err.response['Error']['Message']}. "
                "Check AWS credentials are valid and not expired."
            )

    def test_03_caller_identity_is_role(self, caller_identity):
        """Verify we are running as an IAM role (not user)."""
        arn = caller_identity.get("Arn", "")
        assert ":assumed-role/" in arn or ":role/" in arn, (
            f"Expected to be running as IAM role, but running as: {arn}. "
            "GitHub Actions should assume the GitHub Actions OIDC role."
        )


class TestIAMRoleExistence:
    """Layer 3: Verify the IAM role exists and we can inspect it."""

    def test_01_can_call_iam_get_role_api(self, iam_client, current_role_name):
        """Verify we have permission to call iam:GetRole."""
        if not current_role_name:
            pytest.skip("Could not determine current role name")
        try:
            iam_client.get_role(RoleName=current_role_name)
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "AccessDenied":
                pytest.fail(
                    f"No permission to call iam:GetRole on '{current_role_name}'. "
                    "The role may lack iam:GetRole permission for itself."
                )
            if code == "NoSuchEntity":
                pytest.fail(f"IAM role '{current_role_name}' does not exist.")
            raise

    def test_02_role_exists(self, iam_client, current_role_name):
        """Verify the IAM role exists."""
        if not current_role_name:
            pytest.skip("Could not determine current role name")
        try:
            response = iam_client.get_role(RoleName=current_role_name)
            assert response["Role"]["RoleName"] == current_role_name
        except ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(
                    f"IAM role '{current_role_name}' does not exist. "
                    "Run terraform apply in src/bootstrap/"
                )
            raise


class TestIAMRoleConfiguration:
    """Layer 4: Verify the IAM role has required policies attached."""

    def test_01_can_list_attached_policies(self, iam_client, current_role_name):
        """Verify we can list policies attached to the role."""
        if not current_role_name:
            pytest.skip("Could not determine current role name")
        try:
            iam_client.list_attached_role_policies(RoleName=current_role_name)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to call iam:ListAttachedRolePolicies on '{current_role_name}'. "
                    "Cannot verify role configuration."
                )
            raise

    def test_02_has_administrator_access(self, iam_client, current_role_name):
        """Verify the role has AdministratorAccess policy attached."""
        if not current_role_name:
            pytest.skip("Could not determine current role name")
        try:
            response = iam_client.list_attached_role_policies(RoleName=current_role_name)
            policy_names = [p["PolicyName"] for p in response["AttachedPolicies"]]
            assert "AdministratorAccess" in policy_names, (
                f"Role '{current_role_name}' missing AdministratorAccess policy. "
                f"Attached policies: {policy_names}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDenied":
                pytest.skip("Cannot verify - no permission to list attached policies")
            raise


class TestIAMRoleCapability:
    """Layer 5: Verify the role can perform required actions."""

    def test_01_can_call_s3_list_buckets(self, s3_client):
        """Verify we can call s3:ListBuckets (basic S3 permission check)."""
        try:
            s3_client.list_buckets()
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    "No permission to call s3:ListBuckets. "
                    "The role may lack S3 permissions required for terraform state."
                )
            raise

    def test_02_can_call_ssm_describe_parameters(self, ssm_client):
        """Verify we can call ssm:DescribeParameters (basic SSM permission check)."""
        try:
            ssm_client.describe_parameters(MaxResults=1)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ssm:DescribeParameters. "
                    "The role may lack SSM permissions required to read GitHub PAT."
                )
            raise
