"""Layer 3: Wiring tests.

Verify components are connected properly.
"""
import json

from test.api.endpoints.conftest import assert_lambda_package_includes_file

import pytest
from botocore.exceptions import ClientError



def test_lambda_package_includes_runner_labels(lambda_client, lambda_function_name):
    """Verify deployed Lambda package includes runner_labels.py.

    This is a regression test that validates the deployed Lambda package
    actually contains the runner_labels module. The Lambda will fail at
    runtime with a ModuleNotFoundError if this file is missing.
    """
    response = lambda_client.get_function(FunctionName=lambda_function_name)
    region = response['Configuration']['FunctionArn'].split(':')[3]
    assert_lambda_package_includes_file(lambda_function_name, "runner_labels.py", region)


def test_lambda_kms_key_allows_role(
    lambda_client, kms_client, lambda_function_name, lambda_role_arn
):
    """Verify the KMS key policy allows the Lambda execution role."""
    kms_key_arn = _get_lambda_kms_key_arn(
        lambda_client, kms_client, lambda_function_name
    )
    if not kms_key_arn:
        pytest.skip("Could not determine Lambda KMS key")

    key_id = kms_key_arn.split("/")[-1] if "/" in kms_key_arn else kms_key_arn
    try:
        response = kms_client.get_key_policy(KeyId=key_id, PolicyName="default")
    except ClientError as e:
        pytest.fail(f"Cannot read KMS key policy: {e}")
        return

    policy = json.loads(response.get("Policy", "{}"))
    if not _check_role_allowed_in_key_policy(
        policy.get("Statement", []), lambda_role_arn
    ):
        if not _check_via_service_condition(policy.get("Statement", [])):
            pytest.fail(
                f"KMS key policy does not grant '{lambda_role_arn}' access. "
                f"Add the Lambda execution role to the key policy or use a "
                f"customer-managed key with appropriate permissions."
            )


def _get_lambda_kms_key_arn(lambda_client, kms_client, lambda_function_name: str) -> str:
    """Get the KMS key ARN used by the Lambda function."""
    try:
        func_config = lambda_client.get_function_configuration(
            FunctionName=lambda_function_name
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return ""
        raise

    kms_key_arn = func_config.get("KMSKeyArn")
    has_env_vars = func_config.get("Environment", {}).get("Variables")
    if not has_env_vars:
        return ""
    if not kms_key_arn:
        kms_key_arn = _get_default_lambda_kms_key(kms_client)
    return kms_key_arn


def _get_default_lambda_kms_key(kms_client) -> str:
    """Get the default AWS-managed Lambda KMS key."""
    try:
        response = kms_client.list_aliases()
        for alias in response.get("Aliases", []):
            if alias.get("AliasName") == "alias/aws/lambda":
                return alias.get("TargetKeyId", "")
    except ClientError:
        pass
    return ""


def _check_role_allowed_in_key_policy(statements: list, role_arn: str) -> bool:
    """Check if a role ARN is explicitly allowed in KMS key policy statements."""
    for statement in statements:
        if statement.get("Effect") != "Allow":
            continue
        principals = statement.get("Principal", {})
        if isinstance(principals, str):
            if principals in ("*", role_arn):
                return True
        elif isinstance(principals, dict):
            aws_principals = principals.get("AWS", [])
            if isinstance(aws_principals, str):
                aws_principals = [aws_principals]
            if role_arn in aws_principals or "*" in aws_principals:
                return True
    return False


def _check_via_service_condition(statements: list) -> bool:
    """Check if key policy uses kms:ViaService condition for Lambda."""
    for statement in statements:
        if statement.get("Effect") != "Allow":
            continue
        conditions = statement.get("Condition", {})
        string_equals = conditions.get("StringEquals", {})
        via_service = string_equals.get("kms:ViaService", "")
        if "lambda" in via_service.lower():
            return True
    return False
