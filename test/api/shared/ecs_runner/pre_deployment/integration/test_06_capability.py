"""Layer 6: Capability tests for api/shared/ecs_runner pre-deployment.

Tests that you can perform required operations. Assumes configuration passed.

Six-layer testing model:
- Layer 6: Capability - Can perform required operations
"""

import uuid

from botocore.exceptions import ClientError
import pytest


pytestmark = pytest.mark.layer(6)


class TestIAMCapabilities:
    """Layer 6: Verify we can perform required IAM operations."""

    def test_can_list_buckets(self, s3_client):
        """Verify we can call s3:ListBuckets (basic S3 permission check)."""
        try:
            s3_client.list_buckets()
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    "No permission to call s3:ListBuckets. "
                    "The role may lack S3 permissions required for terraform state."
                )
            raise

    def test_can_list_roles(self, iam_client):
        """Verify we can call iam:ListRoles (basic IAM permission check)."""
        try:
            iam_client.list_roles(MaxItems=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    "No permission to call iam:ListRoles. "
                    "The role may lack IAM permissions required for deployment."
                )
            raise


class TestS3Capabilities:
    """Layer 6: Verify we can read/write to the terraform state bucket."""

    def test_can_list_objects_in_bucket(self, s3_client, state_bucket_name):
        """Verify we can list objects in the state bucket."""
        try:
            s3_client.list_objects_v2(Bucket=state_bucket_name, MaxKeys=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to list objects in '{state_bucket_name}'. "
                    "Check IAM permissions for s3:ListBucket."
                )
            raise

    def test_can_read_state_file(
        self, s3_client, state_bucket_name, ecs_runner_state_key
    ):
        """Verify we can read the api_shared_ecs_runner state file."""
        try:
            s3_client.head_object(Bucket=state_bucket_name, Key=ecs_runner_state_key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "403":
                pytest.fail(
                    f"No permission to read '{ecs_runner_state_key}' "
                    f"from '{state_bucket_name}'. "
                    "Check IAM permissions for s3:GetObject."
                )
            if e.response["Error"]["Code"] == "404":
                # State file doesn't exist yet - that's OK for first deployment
                pytest.skip("State file does not exist yet (first deployment)")
            raise

    def test_can_write_to_bucket(self, s3_client, state_bucket_name):
        """Verify we can write to the state bucket."""
        test_key = f".pre-deployment-test/{uuid.uuid4()}"
        try:
            s3_client.put_object(
                Bucket=state_bucket_name,
                Key=test_key,
                Body=b"pre-deployment-test"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to write to '{state_bucket_name}'. "
                    "Check IAM permissions for s3:PutObject."
                )
            raise
        finally:
            try:
                s3_client.delete_object(Bucket=state_bucket_name, Key=test_key)
            except ClientError:
                pass

    def test_can_delete_from_bucket(self, s3_client, state_bucket_name):
        """Verify we can delete objects from the state bucket."""
        test_key = f".pre-deployment-test/{uuid.uuid4()}"
        try:
            s3_client.put_object(
                Bucket=state_bucket_name,
                Key=test_key,
                Body=b"pre-deployment-test"
            )
            s3_client.delete_object(Bucket=state_bucket_name, Key=test_key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail(
                    f"No permission to delete from '{state_bucket_name}'. "
                    "Check IAM permissions for s3:DeleteObject."
                )
            raise
        finally:
            try:
                s3_client.delete_object(Bucket=state_bucket_name, Key=test_key)
            except ClientError:
                pass


class TestECRCapabilities:
    """Layer 6: Verify we can perform ECR operations."""

    def test_can_create_ecr_repository(self, ecr_client):
        """Verify we can create ECR repositories."""
        test_repo_name = f"pre-deployment-test-{uuid.uuid4().hex[:8]}"
        try:
            ecr_client.create_repository(repositoryName=test_repo_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ecr:CreateRepository. "
                    "Check IAM permissions for ecr:CreateRepository."
                )
            raise
        finally:
            try:
                ecr_client.delete_repository(
                    repositoryName=test_repo_name,
                    force=True
                )
            except ClientError:
                pass

    def test_can_delete_ecr_repository(self, ecr_client):
        """Verify we can delete ECR repositories."""
        test_repo_name = f"pre-deployment-test-{uuid.uuid4().hex[:8]}"
        try:
            ecr_client.create_repository(repositoryName=test_repo_name)
            ecr_client.delete_repository(repositoryName=test_repo_name, force=True)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ecr:DeleteRepository. "
                    "Check IAM permissions for ecr:DeleteRepository."
                )
            raise
        finally:
            try:
                ecr_client.delete_repository(
                    repositoryName=test_repo_name,
                    force=True
                )
            except ClientError:
                pass
