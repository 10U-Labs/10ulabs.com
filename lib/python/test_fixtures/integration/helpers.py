import subprocess
from typing import Any, Callable

from botocore.exceptions import ClientError


def aws_call_error(call: Callable[[], Any], *tolerated_codes: str) -> str:
    try:
        call()
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in tolerated_codes:
            return ""
        return f"{code}: {e.response['Error']['Message']}"
    return ""


def get_aws_account_id_via_cli() -> str:
    result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        check=False,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def s3_head_bucket_problem(s3_client: Any, bucket_name: str) -> str:
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("403", "AccessDenied"):
            return f"No permission to call s3:HeadBucket on '{bucket_name}'"
        if error_code != "404":
            raise
    return ""
