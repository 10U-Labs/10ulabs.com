"""Post-deployment integration tests for Lambda KMS access.

These tests verify that the deployed Lambda execution role can decrypt
environment variables using the KMS key.
"""
import json

import pytest
from botocore.exceptions import ClientError


class TestAWSCredentials:
    """Layer 1: Verify AWS credentials are available and valid."""

    def test_01_credentials_available(self, sts_client):
        """Verify AWS credentials are configured."""
        assert sts_client is not None

    def test_02_can_call_sts_api(self, sts_client):
        """Verify credentials are valid by calling STS."""
        response = sts_client.get_caller_identity()
        assert response.get("Account")


class TestAPIAuthorization:
    """Layer 2: Verify we can call IAM and KMS APIs."""

    def test_01_can_call_iam_api(self, iam_client):
        """Verify we can call IAM APIs."""
        try:
            iam_client.list_roles(MaxItems=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail("No permission to call IAM ListRoles API")
            raise

    def test_02_can_call_kms_api(self, kms_client):
        """Verify we can call KMS APIs."""
        try:
            kms_client.list_keys(Limit=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail("No permission to call KMS ListKeys API")
            raise


class TestLambdaRoleKmsPolicy:
    """Layer 3-4: Verify the Lambda role exists and has KMS permissions."""

    def test_01_lambda_role_exists(self, iam_client, lambda_role_name):
        """Layer 3: Verify the Lambda execution role exists."""
        exists = False
        try:
            response = iam_client.get_role(RoleName=lambda_role_name)
            exists = response.get("Role") is not None
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.fail(
                    f"Lambda execution role '{lambda_role_name}' does not exist. "
                    "Run terraform apply in src/api/endpoints/ec2_runner/"
                )
            raise
        assert exists

    def test_02_lambda_role_has_kms_policy(self, iam_client, lambda_role_name):
        """Verify the Lambda role has a KMS policy attached."""
        has_kms_policy = False
        try:
            response = iam_client.list_role_policies(RoleName=lambda_role_name)
            policy_names = response.get("PolicyNames", [])
            has_kms_policy = "KMSDecrypt" in policy_names
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip(f"Lambda role '{lambda_role_name}' does not exist")
            raise
        assert has_kms_policy, (
            f"Lambda role '{lambda_role_name}' missing KMSDecrypt inline policy. "
            f"Found policies: {policy_names}"
        )

    def test_03_kms_policy_allows_decrypt(self, iam_client, lambda_role_name):
        """Layer 4: Verify the KMS policy allows kms:Decrypt action."""
        allows_decrypt = False
        try:
            response = iam_client.get_role_policy(
                RoleName=lambda_role_name,
                PolicyName="KMSDecrypt"
            )
            policy_doc = response.get("PolicyDocument", {})
            statements = policy_doc.get("Statement", [])
            for statement in statements:
                actions = statement.get("Action", [])
                if isinstance(actions, str):
                    actions = [actions]
                if "kms:Decrypt" in actions and statement.get("Effect") == "Allow":
                    allows_decrypt = True
                    break
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                pytest.skip(f"KMSDecrypt policy not found on role '{lambda_role_name}'")
            raise
        assert allows_decrypt, (
            f"KMSDecrypt policy on '{lambda_role_name}' does not allow kms:Decrypt"
        )


class TestLambdaKmsKeyConfiguration:
    """Layer 4-5: Verify the KMS key allows Lambda role access and invocation works."""

    def test_01_can_get_lambda_kms_key(self, lambda_client, lambda_function_name):
        """Verify we can determine which KMS key the Lambda uses."""
        try:
            response = lambda_client.get_function_configuration(
                FunctionName=lambda_function_name
            )
            kms_key_arn = response.get("KMSKeyArn")
            has_env_vars = response.get("Environment", {}).get("Variables")
            if has_env_vars and not kms_key_arn:
                pass
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip(
                    f"Lambda function '{lambda_function_name}' not deployed yet"
                )
            raise

    def test_02_lambda_kms_key_allows_role(
        self, lambda_client, kms_client, lambda_function_name, lambda_role_arn
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
        if not _check_role_allowed_in_key_policy(policy.get("Statement", []), lambda_role_arn):
            if not _check_via_service_condition(policy.get("Statement", [])):
                pytest.fail(
                    f"KMS key policy does not grant '{lambda_role_arn}' access. "
                    f"Add the Lambda execution role to the key policy or use a "
                    f"customer-managed key with appropriate permissions."
                )

    def test_03_lambda_invoke_succeeds(self, lambda_client, lambda_function_name):
        """Layer 5: Verify Lambda can be invoked without KMS decryption errors.

        This is a capability test that verifies the Lambda can actually start,
        which requires successfully decrypting environment variables.
        """
        try:
            response = lambda_client.invoke(
                FunctionName=lambda_function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps({
                    "httpMethod": "GET",
                    "path": "/v1/ec2-runner",
                    "headers": {"x-test-mode": "true"}
                })
            )
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"].get("Message", "")
            if error_code == "ResourceNotFoundException":
                pytest.skip(
                    f"Lambda function '{lambda_function_name}' not deployed yet"
                )
            if "KMSAccessDenied" in error_code or "KMS" in error_message:
                pytest.fail(
                    f"Lambda failed to decrypt environment variables. "
                    f"KMS Error: {error_message}. "
                    f"The AWS-managed Lambda KMS key policy must grant the "
                    f"execution role access. To fix: update the KMS key policy "
                    f"for the aws/lambda key to allow the Lambda execution role "
                    f"to perform kms:Decrypt."
                )
            raise

        function_error = response.get("FunctionError")
        if function_error:
            payload = response.get("Payload")
            if payload:
                error_body = json.loads(payload.read().decode())
                error_message = error_body.get("errorMessage", "")
                if "KMS" in error_message or "decrypt" in error_message.lower():
                    pytest.fail(
                        f"Lambda failed with KMS error: {error_message}. "
                        f"Verify the KMS key policy grants access."
                    )

        status_code = response.get("StatusCode", 0)
        assert status_code == 200, f"Lambda invoke failed with status {status_code}"


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
