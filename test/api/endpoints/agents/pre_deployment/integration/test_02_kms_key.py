"""Layer 2-4 tests: KMS key for Lambda environment variables.

The agents endpoint Lambda uses KMS to encrypt/decrypt environment variables.
This tests the default AWS-managed Lambda KMS key.

Five-layer testing model:
- Layer 2: Authorization - Can we call KMS APIs?
- Layer 3: Existence - Does the KMS key alias exist?
- Layer 4: Configuration - Is the key enabled and usable?
"""

import pytest
from botocore.exceptions import ClientError


class TestKMSAPIAuthorization:
    """Layer 2: Verify we have permission to call KMS APIs."""

    def test_01_can_call_kms_describe_key(self, kms_client, kms_lambda_key_alias):
        """Verify we have permission to call kms:DescribeKey."""
        try:
            kms_client.describe_key(KeyId=kms_lambda_key_alias)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    f"No permission to call DescribeKey on '{kms_lambda_key_alias}'. "
                    "Check IAM permissions for kms:DescribeKey."
                )
            if err.response["Error"]["Code"] == "NotFoundException":
                pass  # Key doesn't exist, but we have permission - that's OK here
            else:
                raise


class TestKMSKeyExistence:
    """Layer 3: Verify the KMS Lambda key exists."""

    def test_01_kms_lambda_key_alias_exists(self, kms_client, kms_lambda_key_alias):
        """Verify the AWS-managed Lambda KMS key alias exists."""
        try:
            response = kms_client.describe_key(KeyId=kms_lambda_key_alias)
            assert response.get("KeyMetadata") is not None, (
                f"KMS key '{kms_lambda_key_alias}' returned empty response."
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "NotFoundException":
                pytest.fail(
                    f"KMS key alias '{kms_lambda_key_alias}' does not exist. "
                    "The AWS-managed Lambda encryption key should be available."
                )
            raise


class TestKMSKeyConfiguration:
    """Layer 4: Verify the KMS key is configured correctly."""

    def test_01_kms_key_is_enabled(self, kms_client, kms_lambda_key_alias):
        """Verify the KMS key is enabled."""
        try:
            response = kms_client.describe_key(KeyId=kms_lambda_key_alias)
            key_state = response.get("KeyMetadata", {}).get("KeyState", "")
            assert key_state == "Enabled", (
                f"KMS key '{kms_lambda_key_alias}' is in state '{key_state}', "
                "but should be 'Enabled' for Lambda environment encryption."
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "NotFoundException":
                pytest.skip("KMS key not found - covered by existence test")
            raise

    def test_02_kms_key_supports_encrypt_decrypt(self, kms_client, kms_lambda_key_alias):
        """Verify the KMS key supports ENCRYPT_DECRYPT usage."""
        try:
            response = kms_client.describe_key(KeyId=kms_lambda_key_alias)
            key_usage = response.get("KeyMetadata", {}).get("KeyUsage", "")
            assert key_usage == "ENCRYPT_DECRYPT", (
                f"KMS key '{kms_lambda_key_alias}' has usage '{key_usage}', "
                "but should be 'ENCRYPT_DECRYPT' for Lambda environment encryption."
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "NotFoundException":
                pytest.skip("KMS key not found - covered by existence test")
            raise
