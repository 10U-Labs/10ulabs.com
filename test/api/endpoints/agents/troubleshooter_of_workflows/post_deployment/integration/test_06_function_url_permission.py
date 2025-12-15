"""Integration tests for Lambda Function URL permissions.

These tests verify that the Lambda Function URL has the correct resource-based
policy to allow public access.

When using authorization_type = "NONE" for Lambda Function URLs, an explicit
permission is still required in the function's resource policy. Without this,
the Function URL returns 403 Forbidden.

This is a regression test for the missing Function URL permission bug.
"""

import json
import pytest


LAMBDA_FUNCTION_NAME = "TenULabsTroubleshooterOfWorkflowsWebhook"


class TestFunctionURLPermission:
    """Verify Lambda Function URL has public access permission."""

    def test_01_function_url_exists(self, lambda_client):
        """Verify the Lambda has a Function URL configured."""
        try:
            response = lambda_client.get_function_url_config(
                FunctionName=LAMBDA_FUNCTION_NAME
            )
            assert response.get("FunctionUrl"), (
                f"Lambda function '{LAMBDA_FUNCTION_NAME}' has no Function URL configured"
            )
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.fail(
                f"Lambda function '{LAMBDA_FUNCTION_NAME}' not found or has no Function URL"
            )

    def test_02_function_url_auth_type_is_none(self, lambda_client):
        """Verify the Function URL uses NONE authorization type."""
        try:
            response = lambda_client.get_function_url_config(
                FunctionName=LAMBDA_FUNCTION_NAME
            )
            auth_type = response.get("AuthType")
            assert auth_type == "NONE", (
                f"Function URL auth type should be 'NONE' for public access, "
                f"got: {auth_type}"
            )
        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.skip("Lambda function or Function URL not found")

    def test_03_function_has_invoke_url_permission(self, lambda_client):
        """Verify the Lambda has a permission for InvokeFunctionUrl.

        When using authorization_type = "NONE", the Lambda must have a
        resource-based policy statement that allows lambda:InvokeFunctionUrl.
        Without this, the Function URL returns 403 Forbidden.
        """
        try:
            response = lambda_client.get_policy(FunctionName=LAMBDA_FUNCTION_NAME)
            policy = json.loads(response.get("Policy", "{}"))
            statements = policy.get("Statement", [])

            # Look for a statement that allows InvokeFunctionUrl
            has_invoke_url_permission = False
            for stmt in statements:
                action = stmt.get("Action", "")
                if isinstance(action, list):
                    actions = action
                else:
                    actions = [action]

                if "lambda:InvokeFunctionUrl" in actions:
                    has_invoke_url_permission = True
                    break

            assert has_invoke_url_permission, (
                f"Lambda function '{LAMBDA_FUNCTION_NAME}' is missing "
                "lambda:InvokeFunctionUrl permission in its resource policy.\n\n"
                "When using Function URL with authorization_type = 'NONE', "
                "you must add an aws_lambda_permission resource:\n\n"
                "  resource \"aws_lambda_permission\" \"function_url\" {\n"
                "    statement_id           = \"FunctionURLAllowPublicAccess\"\n"
                "    action                 = \"lambda:InvokeFunctionUrl\"\n"
                "    function_name          = aws_lambda_function.<name>.function_name\n"
                "    principal              = \"*\"\n"
                "    function_url_auth_type = \"NONE\"\n"
                "  }\n\n"
                "Without this, the Function URL returns 403 Forbidden."
            )

        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.fail(
                f"Lambda function '{LAMBDA_FUNCTION_NAME}' not found or has no policy. "
                "A policy with lambda:InvokeFunctionUrl is required for Function URL access."
            )

    def test_04_invoke_url_permission_allows_public_access(self, lambda_client):
        """Verify the InvokeFunctionUrl permission has public principal.

        The permission should have Principal: "*" to allow anyone to invoke.
        """
        try:
            response = lambda_client.get_policy(FunctionName=LAMBDA_FUNCTION_NAME)
            policy = json.loads(response.get("Policy", "{}"))
            statements = policy.get("Statement", [])

            for stmt in statements:
                action = stmt.get("Action", "")
                if isinstance(action, list):
                    actions = action
                else:
                    actions = [action]

                if "lambda:InvokeFunctionUrl" not in actions:
                    continue

                # Check principal allows public access
                principal = stmt.get("Principal", {})
                if isinstance(principal, str):
                    allows_public = principal == "*"
                else:
                    allows_public = principal.get("AWS") == "*" or principal == "*"

                assert allows_public, (
                    "InvokeFunctionUrl permission does not allow public access. "
                    f"Principal should be '*', got: {principal}"
                )
                return  # Found valid permission

            pytest.fail("No valid InvokeFunctionUrl permission found")

        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.skip("Lambda function not found or has no policy")

    def test_05_invoke_url_permission_has_correct_auth_type(self, lambda_client):
        """Verify the InvokeFunctionUrl permission has correct auth type condition.

        If a FunctionUrlAuthType condition is present, it should be "NONE".
        """
        try:
            response = lambda_client.get_policy(FunctionName=LAMBDA_FUNCTION_NAME)
            policy = json.loads(response.get("Policy", "{}"))
            statements = policy.get("Statement", [])

            for stmt in statements:
                action = stmt.get("Action", "")
                if isinstance(action, list):
                    actions = action
                else:
                    actions = [action]

                if "lambda:InvokeFunctionUrl" not in actions:
                    continue

                # Check FunctionUrlAuthType condition if present
                conditions = stmt.get("Condition", {})
                auth_type_condition = conditions.get("StringEquals", {}).get(
                    "lambda:FunctionUrlAuthType"
                )
                if auth_type_condition:
                    assert auth_type_condition == "NONE", (
                        f"FunctionUrlAuthType condition should be 'NONE', "
                        f"got: {auth_type_condition}"
                    )
                return  # Found permission, condition check passed or not present

            pytest.skip("No InvokeFunctionUrl permission found to check")

        except lambda_client.exceptions.ResourceNotFoundException:
            pytest.skip("Lambda function not found or has no policy")
