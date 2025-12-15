"""Layer 2-4 tests: GitHub App SSM Parameters.

The agents endpoint Lambda reads GitHub App credentials from SSM parameters
to authenticate with GitHub for workflow troubleshooting and PR creation.

Five-layer testing model:
- Layer 2: Authorization - Can we call SSM APIs?
- Layer 3: Existence - Do the SSM parameters exist?
- Layer 4: Configuration - Are parameters configured correctly (SecureString)?
"""

import pytest
from botocore.exceptions import ClientError


class TestSSMGitHubAppAuthorization:
    """Layer 2: Verify we have permission to access SSM parameters."""

    def test_01_can_call_get_parameter_api(self, ssm_client, github_app_ssm_id_name):
        """Verify we have permission to call ssm:GetParameter."""
        try:
            ssm_client.get_parameter(Name=github_app_ssm_id_name, WithDecryption=False)
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "AccessDeniedException":
                pytest.fail(
                    f"No permission to call GetParameter on '{github_app_ssm_id_name}'. "
                    "Check IAM permissions for ssm:GetParameter."
                )
            if code == "ParameterNotFound":
                pass  # Parameter doesn't exist, but we have permission - that's OK here
            else:
                raise


class TestSSMGitHubAppExistence:
    """Layer 3: Verify the GitHub App SSM parameters exist."""

    def test_01_github_app_id_parameter_exists(self, ssm_client, github_app_ssm_id_name):
        """Verify the GitHub App ID SSM parameter exists."""
        try:
            response = ssm_client.get_parameter(
                Name=github_app_ssm_id_name, WithDecryption=False
            )
            assert response.get("Parameter") is not None, (
                f"SSM parameter '{github_app_ssm_id_name}' returned empty response."
            )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "ParameterNotFound":
                pytest.fail(
                    f"SSM parameter '{github_app_ssm_id_name}' does not exist. "
                    "This parameter must be created with the GitHub App ID."
                )
            raise

    def test_02_github_app_installation_id_parameter_exists(
        self, ssm_client, github_app_ssm_installation_id_name
    ):
        """Verify the GitHub App Installation ID SSM parameter exists."""
        try:
            response = ssm_client.get_parameter(
                Name=github_app_ssm_installation_id_name, WithDecryption=False
            )
            assert response.get("Parameter") is not None, (
                f"SSM parameter '{github_app_ssm_installation_id_name}' returned empty response."
            )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "ParameterNotFound":
                pytest.fail(
                    f"SSM parameter '{github_app_ssm_installation_id_name}' does not exist. "
                    "This parameter must be created with the GitHub App Installation ID."
                )
            raise

    def test_03_github_app_private_key_parameter_exists(
        self, ssm_client, github_app_ssm_private_key_name
    ):
        """Verify the GitHub App Private Key SSM parameter exists."""
        try:
            response = ssm_client.get_parameter(
                Name=github_app_ssm_private_key_name, WithDecryption=False
            )
            assert response.get("Parameter") is not None, (
                f"SSM parameter '{github_app_ssm_private_key_name}' returned empty response."
            )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "ParameterNotFound":
                pytest.fail(
                    f"SSM parameter '{github_app_ssm_private_key_name}' does not exist. "
                    "This parameter must be created with the GitHub App Private Key."
                )
            raise


class TestSSMGitHubAppConfiguration:
    """Layer 4: Verify the GitHub App SSM parameters are configured correctly."""

    def test_01_github_app_id_is_secure_string(
        self, ssm_client, github_app_ssm_id_name
    ):
        """Verify the GitHub App ID is stored as SecureString."""
        try:
            response = ssm_client.get_parameter(
                Name=github_app_ssm_id_name, WithDecryption=False
            )
            param_type = response.get("Parameter", {}).get("Type", "")
            assert param_type == "SecureString", (
                f"SSM parameter '{github_app_ssm_id_name}' is type '{param_type}', "
                "but should be 'SecureString' for security."
            )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "ParameterNotFound":
                pytest.skip("Parameter does not exist - covered by existence test")
            raise

    def test_02_github_app_installation_id_is_secure_string(
        self, ssm_client, github_app_ssm_installation_id_name
    ):
        """Verify the GitHub App Installation ID is stored as SecureString."""
        try:
            response = ssm_client.get_parameter(
                Name=github_app_ssm_installation_id_name, WithDecryption=False
            )
            param_type = response.get("Parameter", {}).get("Type", "")
            assert param_type == "SecureString", (
                f"SSM parameter '{github_app_ssm_installation_id_name}' is type '{param_type}', "
                "but should be 'SecureString' for security."
            )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "ParameterNotFound":
                pytest.skip("Parameter does not exist - covered by existence test")
            raise

    def test_03_github_app_private_key_is_secure_string(
        self, ssm_client, github_app_ssm_private_key_name
    ):
        """Verify the GitHub App Private Key is stored as SecureString."""
        try:
            response = ssm_client.get_parameter(
                Name=github_app_ssm_private_key_name, WithDecryption=False
            )
            param_type = response.get("Parameter", {}).get("Type", "")
            assert param_type == "SecureString", (
                f"SSM parameter '{github_app_ssm_private_key_name}' is type '{param_type}', "
                "but should be 'SecureString' for security."
            )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "ParameterNotFound":
                pytest.skip("Parameter does not exist - covered by existence test")
            raise

    def test_04_github_app_id_has_value(self, ssm_client, github_app_ssm_id_name):
        """Verify the GitHub App ID SSM parameter has a non-empty value."""
        try:
            response = ssm_client.get_parameter(
                Name=github_app_ssm_id_name, WithDecryption=True
            )
            value = response.get("Parameter", {}).get("Value", "")
            assert value, (
                f"SSM parameter '{github_app_ssm_id_name}' exists but has empty value."
            )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "ParameterNotFound":
                pytest.skip("Parameter does not exist - covered by existence test")
            if code == "AccessDeniedException":
                pytest.skip("No permission to decrypt - checking existence only")
            raise
