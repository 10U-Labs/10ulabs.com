import subprocess

import pytest
from botocore.exceptions import ClientError, NoCredentialsError


NO_CREDENTIALS_MESSAGE = (
    "No AWS credentials found. "
    "Configure credentials via environment variables, "
    "~/.aws/credentials, or IAM role."
)


def check_lambda_function_exists(lambda_client, function_name: str, terraform_path: str):
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        assert response["Configuration"]["FunctionName"] == function_name
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            pytest.fail(
                f"Lambda function '{function_name}' does not exist. "
                f"Run terraform apply in {terraform_path}"
            )
        raise


def check_iam_role_exists(iam_client, role_name: str, terraform_path: str):
    try:
        response = iam_client.get_role(RoleName=role_name)
        assert response.get("Role") is not None
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            pytest.fail(
                f"Lambda execution role '{role_name}' does not exist. "
                f"Run terraform apply in {terraform_path}"
            )
        raise


def check_lambda_role_has_policy(iam_client, role_name: str, policy_name: str):
    try:
        response = iam_client.list_role_policies(RoleName=role_name)
        policy_names = response.get("PolicyNames", [])
        assert policy_name in policy_names, (
            f"Lambda role '{role_name}' missing {policy_name} inline policy. "
            f"Found policies: {policy_names}"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            pytest.skip(f"Lambda role '{role_name}' does not exist")
        raise


def _fail_no_credentials():
    pytest.fail(NO_CREDENTIALS_MESSAGE)


def check_credentials_available(sts_client):
    try:
        sts_client.get_caller_identity()
    except NoCredentialsError:
        _fail_no_credentials()


def check_credentials_valid(sts_client):
    try:
        sts_client.get_caller_identity()
    except ClientError as e:
        pytest.fail(
            f"Failed to call sts:GetCallerIdentity: "
            f"{e.response['Error']['Message']}. "
            "Check AWS credentials are valid and not expired."
        )


def check_service_can_assume_role(trust_policy, service_name):
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
    result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        check=False,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def handle_ecr_authorization_error(error: ClientError, operation: str, repository_name: str):
    error_code = error.response["Error"]["Code"]
    if error_code == "AccessDeniedException":
        pytest.fail(
            f"No permission to call {operation} on '{repository_name}'. "
            "Check IAM policy."
        )
    if error_code == "RepositoryNotFoundException":
        pass
    else:
        raise error


def check_s3_head_bucket_permission(s3_client, bucket_name: str):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("403", "AccessDenied"):
            pytest.fail(f"No permission to call s3:HeadBucket on '{bucket_name}'")
        if error_code != "404":
            raise


def skip_if_api_gateway_unavailable(api_gateway_info):
    if api_gateway_info.get("id") is None:
        pytest.skip("api_gateway_id output not available")
    if not api_gateway_info.get("exists"):
        pytest.skip("API Gateway does not exist")


def check_state_file_readable(s3_client, bucket_name: str, state_key: str):
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


def assert_api_gateway_exists(api_gateway_info, terraform_path: str = "src/api/common/routing/"):
    if api_gateway_info.get("id") is None:
        pytest.skip("api_gateway_id output not available")
    assert api_gateway_info.get("exists"), (
        f"API Gateway '{api_gateway_info['id']}' does not exist. "
        f"Run terraform apply in {terraform_path}"
    )
