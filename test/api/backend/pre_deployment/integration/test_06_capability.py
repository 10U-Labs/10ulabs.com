"""Layer 6: Capability tests for api_backend pre-deployment validation.

Verify we can perform required operations (assumes configuration passed).
"""
import uuid

import pytest
from botocore.exceptions import ClientError

pytestmark = pytest.mark.dependency(
    name="layer6", depends=["layer1", "layer2", "layer3", "layer4", "layer5"]
)


def test_can_call_s3_list_buckets(s3_client):
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


def test_can_call_iam_list_roles(iam_client):
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


def test_can_list_state_bucket_objects(s3_client, state_bucket_name):
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


def test_can_read_state_file(s3_client, state_bucket_name):
    """Verify we can read the api_backend state file."""
    state_key = "api/terraform.tfstate"
    try:
        s3_client.head_object(Bucket=state_bucket_name, Key=state_key)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "403":
            pytest.fail(
                f"No permission to read '{state_key}' from '{state_bucket_name}'. "
                "Check IAM permissions for s3:GetObject."
            )
        if error_code == "404":
            pytest.skip("State file does not exist yet (first deployment)")
        raise


def test_can_write_to_state_bucket(s3_client, state_bucket_name):
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


def test_can_delete_from_state_bucket(s3_client, state_bucket_name):
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


def test_can_write_to_central_logs_bucket(s3_client, central_logs_bucket_name):
    """Verify we can write to the central logs bucket (needed for Firehose)."""
    if not central_logs_bucket_name:
        pytest.skip("central_logs_bucket_name not available")
    test_key = f"pre-deployment-test/{uuid.uuid4()}"
    try:
        s3_client.put_object(
            Bucket=central_logs_bucket_name,
            Key=test_key,
            Body=b"test-write"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail(
                f"No permission to write to '{central_logs_bucket_name}'. "
                "Firehose delivery will fail without write access. "
                "Check IAM permissions for s3:PutObject."
            )
        raise
    finally:
        try:
            s3_client.delete_object(Bucket=central_logs_bucket_name, Key=test_key)
        except ClientError:
            pass


def test_can_delete_from_central_logs_bucket(s3_client, central_logs_bucket_name):
    """Verify we can delete from the central logs bucket (needed for cleanup)."""
    if not central_logs_bucket_name:
        pytest.skip("central_logs_bucket_name not available")
    test_key = f"pre-deployment-test/{uuid.uuid4()}"
    try:
        s3_client.put_object(
            Bucket=central_logs_bucket_name,
            Key=test_key,
            Body=b"test-delete"
        )
        s3_client.delete_object(Bucket=central_logs_bucket_name, Key=test_key)
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            pytest.fail(
                f"No permission to delete from '{central_logs_bucket_name}'. "
                "Check IAM permissions for s3:DeleteObject."
            )
        raise
    finally:
        try:
            s3_client.delete_object(Bucket=central_logs_bucket_name, Key=test_key)
        except ClientError:
            pass
