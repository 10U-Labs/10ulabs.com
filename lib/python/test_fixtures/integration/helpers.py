"""Shared helper functions and constants for integration tests."""
import subprocess

import pytest
from botocore.exceptions import ClientError, NoCredentialsError


# Shared error messages
NO_CREDENTIALS_MESSAGE = (
    "No AWS credentials found. "
    "Configure credentials via environment variables, "
    "~/.aws/credentials, or IAM role."
)


def fail_no_credentials():
    """Fail the test with a standard no-credentials message."""
    pytest.fail(NO_CREDENTIALS_MESSAGE)


def check_credentials_available(sts_client):
    """Check if AWS credentials are available and valid.

    Args:
        sts_client: boto3 STS client

    Raises:
        pytest.fail: If credentials are not available or invalid
    """
    try:
        sts_client.get_caller_identity()
    except NoCredentialsError:
        fail_no_credentials()


def check_credentials_valid(sts_client):
    """Check if AWS credentials are valid by calling STS.

    Args:
        sts_client: boto3 STS client

    Raises:
        pytest.fail: If credentials are invalid or expired
    """
    try:
        sts_client.get_caller_identity()
    except ClientError as e:
        pytest.fail(
            f"Failed to call sts:GetCallerIdentity: "
            f"{e.response['Error']['Message']}. "
            "Check AWS credentials are valid and not expired."
        )


def check_service_can_assume_role(trust_policy, service_name):
    """Check if a service can assume a role based on trust policy.

    Args:
        trust_policy: IAM role trust policy document
        service_name: AWS service name (e.g., 'lambda.amazonaws.com')

    Returns:
        True if the service can assume the role, False otherwise
    """
    statements = trust_policy.get("Statement", [])
    for statement in statements:
        if statement.get("Effect") != "Allow":
            continue
        principals = statement.get("Principal", {})
        service = principals.get("Service", [])
        if isinstance(service, str):
            service = [service]
        if service_name in service:
            return True
    return False


def get_aws_account_id_via_cli():
    """Get AWS account ID using the AWS CLI.

    Returns:
        AWS account ID as a string, or empty string on failure.
    """
    result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        check=False,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def handle_ecr_authorization_error(error: ClientError, operation: str, repository_name: str):
    """Handle ECR authorization errors in Layer 2 tests.

    Args:
        error: The ClientError that was raised
        operation: ECR operation name (e.g., "ecr:DescribeRepositories")
        repository_name: Name of the ECR repository

    Raises:
        pytest.fail: If access is denied
        ClientError: Re-raises for other error codes besides RepositoryNotFoundException
    """
    error_code = error.response["Error"]["Code"]
    if error_code == "AccessDeniedException":
        pytest.fail(
            f"No permission to call {operation} on '{repository_name}'. "
            "Check IAM policy."
        )
    if error_code == "RepositoryNotFoundException":
        pass  # Repository doesn't exist, but we have permission - OK for layer 2
    else:
        raise error


def check_s3_head_bucket_permission(s3_client, bucket_name: str):
    """Check permission to call s3:HeadBucket on a bucket.

    Used by Layer 2 authorization tests to verify S3 permissions.

    Args:
        s3_client: boto3 S3 client
        bucket_name: Name of the S3 bucket to check

    Raises:
        pytest.fail: If access is denied (403 or AccessDenied)
        ClientError: Re-raises for other error codes besides 404
    """
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("403", "AccessDenied"):
            pytest.fail(f"No permission to call s3:HeadBucket on '{bucket_name}'")
        if error_code != "404":
            raise


def skip_if_api_gateway_unavailable(api_gateway_info):
    """Skip test if API Gateway info is unavailable or API doesn't exist.

    Use this helper in Layer 4/5 tests to avoid duplicating skip logic.

    Args:
        api_gateway_info: Dictionary with 'id' and 'exists' keys

    Returns:
        True if the test should continue, False if skipped
    """
    if api_gateway_info.get("id") is None:
        pytest.skip("api_gateway_rest_api_id output not available")
        return False
    if not api_gateway_info.get("exists"):
        pytest.skip("API Gateway does not exist")
        return False
    return True


def check_state_file_readable(s3_client, bucket_name: str, state_key: str):
    """Check if a Terraform state file can be read from S3.

    Used by Layer 6 capability tests to verify state file access.
    Handles permission errors and missing files appropriately.

    Args:
        s3_client: boto3 S3 client
        bucket_name: Name of the S3 bucket
        state_key: Key path to the state file

    Raises:
        pytest.fail: If access is denied (403)
        pytest.skip: If state file doesn't exist (first deployment)
        ClientError: Re-raises for other errors
    """
    try:
        s3_client.head_object(Bucket=bucket_name, Key=state_key)
    except ClientError as e:
        if e.response["Error"]["Code"] == "403":
            pytest.fail(
                f"No permission to read '{state_key}' from '{bucket_name}'. "
                "Check IAM permissions for s3:GetObject."
            )
        if e.response["Error"]["Code"] == "404":
            pytest.skip("State file does not exist yet (first deployment)")
        raise


def assert_api_gateway_exists(api_gateway_info, terraform_path: str = "src/api/backend/"):
    """Assert that API Gateway exists, skipping if ID is not available.

    Use this in Layer 4/5 existence tests to verify API Gateway presence.

    Args:
        api_gateway_info: Dictionary with 'id' and 'exists' keys
        terraform_path: Path to terraform for error message

    Raises:
        pytest.skip: If api_gateway_rest_api_id output is not available
        AssertionError: If API Gateway doesn't exist
    """
    if api_gateway_info.get("id") is None:
        pytest.skip("api_gateway_rest_api_id output not available")
    assert api_gateway_info.get("exists"), (
        f"API Gateway '{api_gateway_info['id']}' does not exist. "
        f"Run terraform apply in {terraform_path}"
    )


def assert_iam_role_name_is_pascalcase(iam_client, role_name: str, validate_name_func):
    """Assert that an IAM role name follows PascalCase naming convention.

    Use this in naming convention tests to verify IAM role names.

    Args:
        iam_client: boto3 IAM client
        role_name: Name of the IAM role to check
        validate_name_func: Function that validates the name and returns error or None

    Raises:
        AssertionError: If role name doesn't follow PascalCase
    """
    response = iam_client.get_role(RoleName=role_name)
    actual_name = response['Role']['RoleName']
    error = validate_name_func(actual_name)
    assert error is None, (
        f"Deployed IAM role has invalid name '{actual_name}': {error}"
    )
