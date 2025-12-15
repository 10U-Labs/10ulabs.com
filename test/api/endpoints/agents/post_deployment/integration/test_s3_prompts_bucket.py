"""Post-deployment integration tests: S3 Prompts Bucket.

Verifies the S3 bucket for agent prompts is deployed and configured correctly.

Five-layer testing model:
- Layer 3: Existence - Does the S3 bucket exist?
- Layer 4: Configuration - Is versioning/encryption enabled? Are prompts uploaded?
"""

import pytest
from botocore.exceptions import ClientError


class TestS3PromptsBucketExistence:
    """Layer 3: Verify the S3 prompts bucket exists."""

    def test_01_prompts_bucket_exists(self, s3_client, s3_prompts_bucket_name):
        """Verify the prompts S3 bucket exists."""
        try:
            s3_client.head_bucket(Bucket=s3_prompts_bucket_name)
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code in ("404", "NoSuchBucket"):
                pytest.fail(
                    f"S3 bucket '{s3_prompts_bucket_name}' does not exist. "
                    "Run terraform apply to create it."
                )
            raise


class TestS3PromptsBucketConfiguration:
    """Layer 4: Verify the S3 prompts bucket is configured correctly."""

    def test_01_bucket_has_versioning_enabled(self, s3_client, s3_prompts_bucket_name):
        """Verify the prompts bucket has versioning enabled."""
        try:
            response = s3_client.get_bucket_versioning(Bucket=s3_prompts_bucket_name)
            status = response.get("Status", "")
            assert status == "Enabled", (
                f"S3 bucket '{s3_prompts_bucket_name}' should have versioning enabled. "
                f"Current status: {status or 'Disabled'}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] in ("404", "NoSuchBucket"):
                pytest.skip("Bucket not found - covered by existence test")
            raise

    def test_02_bucket_has_encryption_enabled(self, s3_client, s3_prompts_bucket_name):
        """Verify the prompts bucket has server-side encryption enabled."""
        try:
            response = s3_client.get_bucket_encryption(Bucket=s3_prompts_bucket_name)
            rules = response.get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
            assert len(rules) > 0, (
                f"S3 bucket '{s3_prompts_bucket_name}' should have encryption enabled."
            )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "ServerSideEncryptionConfigurationNotFoundError":
                pytest.fail(
                    f"S3 bucket '{s3_prompts_bucket_name}' has no encryption configured."
                )
            if code in ("404", "NoSuchBucket"):
                pytest.skip("Bucket not found - covered by existence test")
            raise

    def test_03_bucket_blocks_public_acls(self, s3_client, s3_prompts_bucket_name):
        """Verify the prompts bucket blocks public ACLs."""
        try:
            response = s3_client.get_public_access_block(Bucket=s3_prompts_bucket_name)
            config = response.get("PublicAccessBlockConfiguration", {})
            assert config.get("BlockPublicAcls", False), "BlockPublicAcls should be enabled"
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "NoSuchPublicAccessBlockConfiguration":
                pytest.fail(
                    f"S3 bucket '{s3_prompts_bucket_name}' has no public access block configured."
                )
            if code in ("404", "NoSuchBucket"):
                pytest.skip("Bucket not found - covered by existence test")
            raise

    def test_04_bucket_blocks_public_policy(self, s3_client, s3_prompts_bucket_name):
        """Verify the prompts bucket blocks public policy."""
        try:
            response = s3_client.get_public_access_block(Bucket=s3_prompts_bucket_name)
            config = response.get("PublicAccessBlockConfiguration", {})
            assert config.get("BlockPublicPolicy", False), "BlockPublicPolicy should be enabled"
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "NoSuchPublicAccessBlockConfiguration":
                pytest.fail(
                    f"S3 bucket '{s3_prompts_bucket_name}' has no public access block configured."
                )
            if code in ("404", "NoSuchBucket"):
                pytest.skip("Bucket not found - covered by existence test")
            raise

    def test_05_bucket_ignores_public_acls(self, s3_client, s3_prompts_bucket_name):
        """Verify the prompts bucket ignores public ACLs."""
        try:
            response = s3_client.get_public_access_block(Bucket=s3_prompts_bucket_name)
            config = response.get("PublicAccessBlockConfiguration", {})
            assert config.get("IgnorePublicAcls", False), "IgnorePublicAcls should be enabled"
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "NoSuchPublicAccessBlockConfiguration":
                pytest.fail(
                    f"S3 bucket '{s3_prompts_bucket_name}' has no public access block configured."
                )
            if code in ("404", "NoSuchBucket"):
                pytest.skip("Bucket not found - covered by existence test")
            raise

    def test_06_bucket_restricts_public_buckets(self, s3_client, s3_prompts_bucket_name):
        """Verify the prompts bucket restricts public buckets."""
        try:
            response = s3_client.get_public_access_block(Bucket=s3_prompts_bucket_name)
            config = response.get("PublicAccessBlockConfiguration", {})
            assert config.get("RestrictPublicBuckets", False), "RestrictPublicBuckets should be enabled"
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "NoSuchPublicAccessBlockConfiguration":
                pytest.fail(
                    f"S3 bucket '{s3_prompts_bucket_name}' has no public access block configured."
                )
            if code in ("404", "NoSuchBucket"):
                pytest.skip("Bucket not found - covered by existence test")
            raise

    def test_07_prompts_are_uploaded(self, s3_client, s3_prompts_bucket_name):
        """Verify agent prompts are uploaded to the bucket."""
        try:
            response = s3_client.list_objects_v2(
                Bucket=s3_prompts_bucket_name,
                Prefix="prompts/",
                MaxKeys=10
            )
            contents = response.get("Contents", [])
            prompt_files = [obj["Key"] for obj in contents if obj["Key"].endswith(".md")]
            assert len(prompt_files) >= 2, (
                f"Expected at least 2 prompt files in '{s3_prompts_bucket_name}/prompts/', "
                f"found {len(prompt_files)}: {prompt_files}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] in ("404", "NoSuchBucket"):
                pytest.skip("Bucket not found - covered by existence test")
            raise

    def test_08_troubleshooter_prompt_exists(self, s3_client, s3_prompts_bucket_name):
        """Verify troubleshooter_of_workflows prompt is uploaded."""
        try:
            s3_client.head_object(
                Bucket=s3_prompts_bucket_name,
                Key="prompts/troubleshooter_of_workflows.md"
            )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "404":
                pytest.fail(
                    "troubleshooter_of_workflows.md prompt not found in S3. "
                    "Run terraform apply to upload prompts."
                )
            if code == "NoSuchBucket":
                pytest.skip("Bucket not found - covered by existence test")
            raise

    def test_09_creator_prompt_exists(self, s3_client, s3_prompts_bucket_name):
        """Verify creator_of_agents prompt is uploaded."""
        try:
            s3_client.head_object(
                Bucket=s3_prompts_bucket_name,
                Key="prompts/creator_of_agents.md"
            )
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code == "404":
                pytest.fail(
                    "creator_of_agents.md prompt not found in S3. "
                    "Run terraform apply to upload prompts."
                )
            if code == "NoSuchBucket":
                pytest.skip("Bucket not found - covered by existence test")
            raise
