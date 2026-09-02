from typing import Any

from botocore.exceptions import ClientError


def test_terraform_state_capability(s3_client: Any, state_bucket_name: str) -> None:
    has_capability = True
    try:
        s3_client.list_objects_v2(
            Bucket=state_bucket_name,
            MaxKeys=1
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            has_capability = False
        else:
            raise
    assert has_capability, (
        f"No permission to read from state bucket '{state_bucket_name}'. "
        "Check IAM permissions for s3:ListBucket."
    )
