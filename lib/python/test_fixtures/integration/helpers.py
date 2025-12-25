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
