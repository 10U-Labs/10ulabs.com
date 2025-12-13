"""Tests to validate GitHub PAT SSM parameter exists.

These tests verify that the GitHub Personal Access Token SSM parameter
exists and is accessible. This is a REQUIRED prerequisite (no defaults
in data.tf) for the runners endpoint - it's used by 6 Lambda functions.

Five-layer testing model:
- Layer 2: Authorization - Can we call SSM APIs?
- Layer 3: Existence - Does the SSM parameter exist?
"""

import pytest
from botocore.exceptions import ClientError


class TestSSMGitHubPATAuthorization:  # pylint: disable=too-few-public-methods
    """Layer 2: Verify we have permission to access SSM parameters."""

    def test_01_can_call_get_parameter_api(self, ssm_client, ssm_github_pat_name):
        """Layer 2: Verify we have permission to call ssm:GetParameter."""
        try:
            ssm_client.get_parameter(Name=ssm_github_pat_name, WithDecryption=False)
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "AccessDeniedException":
                pytest.fail(
                    f"No permission to call GetParameter on '{ssm_github_pat_name}'. "
                    "Check IAM permissions for ssm:GetParameter."
                )
            if code == "ParameterNotFound":
                pass  # Parameter doesn't exist, but we have permission - that's OK here
            else:
                raise


class TestSSMGitHubPATExistence:
    """Layer 3: Verify the GitHub PAT SSM parameter exists."""

    def test_01_github_pat_parameter_exists(self, ssm_client, ssm_github_pat_name):
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

    def test_02_github_pat_parameter_has_value(self, ssm_client, ssm_github_pat_name):
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

    def test_03_github_pat_parameter_is_secure_string(
        self, ssm_client, ssm_github_pat_name
    ):
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
