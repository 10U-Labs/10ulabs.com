"""Tests to validate SSM GitHub PAT parameter before workflow_fixer deployment.

Five-layer testing model:
- Layer 2: Authorization - Can we call SSM APIs?
- Layer 3: Existence - Does the parameter exist?
- Layer 4: Configuration - Is it configured correctly (SecureString)?
- Layer 5: Capability - Can we read the parameter value?
"""

from botocore.exceptions import ClientError
import pytest


class TestSSMParameterAuthorization:
    """Layer 2: Verify we can call SSM APIs."""

    def test_01_can_call_describe_parameters_api(self, ssm_client):
        """Verify we have permission to call ssm:DescribeParameters."""
        try:
            ssm_client.describe_parameters(MaxResults=1)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call DescribeParameters. "
                    "Check IAM permissions for ssm:DescribeParameters."
                )
            raise

    def test_02_can_call_get_parameter_api(self, ssm_client, ssm_github_pat_name):
        """Verify we have permission to call ssm:GetParameter."""
        try:
            ssm_client.get_parameter(Name=ssm_github_pat_name, WithDecryption=False)
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "AccessDeniedException":
                pytest.fail(
                    f"No permission to call GetParameter on '{ssm_github_pat_name}'. "
                    "Check IAM permissions for ssm:GetParameter."
                )
            if code == "ParameterNotFound":
                pass  # Existence check is in next layer
            else:
                raise


class TestSSMParameterExistence:
    """Layer 3: Verify the SSM parameter exists."""

    def test_01_parameter_exists(self, ssm_client, ssm_github_pat_name):
        """Verify the GitHub PAT parameter exists."""
        try:
            ssm_client.get_parameter(Name=ssm_github_pat_name, WithDecryption=False)
        except ClientError as err:
            if err.response["Error"]["Code"] == "ParameterNotFound":
                pytest.fail(
                    f"SSM parameter '{ssm_github_pat_name}' does not exist. "
                    "Create the parameter with: "
                    f"aws ssm put-parameter --name {ssm_github_pat_name} "
                    "--type SecureString --value <github_pat>"
                )
            raise


class TestSSMParameterConfiguration:
    """Layer 4: Verify the SSM parameter is configured correctly."""

    def test_01_parameter_is_secure_string(self, ssm_client, ssm_github_pat_name):
        """Verify the parameter is a SecureString (encrypted)."""
        try:
            response = ssm_client.get_parameter(
                Name=ssm_github_pat_name, WithDecryption=False
            )
            param_type = response["Parameter"]["Type"]
            assert param_type == "SecureString", (
                f"Parameter '{ssm_github_pat_name}' is type '{param_type}', "
                "expected 'SecureString'. GitHub PAT should be encrypted."
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ParameterNotFound":
                pytest.skip("Parameter does not exist")
            raise

    def test_02_parameter_has_value(self, ssm_client, ssm_github_pat_name):
        """Verify the parameter has a non-empty value."""
        try:
            response = ssm_client.get_parameter(
                Name=ssm_github_pat_name, WithDecryption=False
            )
            # Check the encrypted value exists (don't decrypt in test)
            value = response["Parameter"].get("Value", "")
            assert value, (
                f"Parameter '{ssm_github_pat_name}' has empty value. "
                "Update with a valid GitHub PAT."
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ParameterNotFound":
                pytest.skip("Parameter does not exist")
            raise


class TestSSMParameterCapability:
    """Layer 5: Verify we can read the decrypted parameter value."""

    def test_01_can_decrypt_parameter(self, ssm_client, ssm_github_pat_name):
        """Verify we can read the decrypted GitHub PAT value."""
        try:
            response = ssm_client.get_parameter(
                Name=ssm_github_pat_name, WithDecryption=True
            )
            value = response["Parameter"]["Value"]
            # Don't log the actual value, just verify it looks like a PAT
            assert value.startswith("ghp_") or value.startswith("github_pat_"), (
                f"Parameter '{ssm_github_pat_name}' value doesn't look like a "
                "GitHub PAT (should start with 'ghp_' or 'github_pat_')."
            )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "ParameterNotFound":
                pytest.skip("Parameter does not exist")
            if code == "AccessDeniedException":
                pytest.fail(
                    f"No permission to decrypt '{ssm_github_pat_name}'. "
                    "Check IAM permissions for kms:Decrypt on the SSM key."
                )
            raise
