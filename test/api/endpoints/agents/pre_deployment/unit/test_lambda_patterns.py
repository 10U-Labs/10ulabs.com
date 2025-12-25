"""Unit tests for Lambda patterns in agents endpoint."""
from repo_utils import REPO_ROOT
from test_fixtures.lambda_lifecycle import create_lambda_lifecycle_tests

AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


# Use shared Lambda lifecycle tests
TestLambdaLifecycleRules = create_lambda_lifecycle_tests(endpoint_src=AGENTS_SRC)


class TestFunctionURLPermissions:
    """Tests for Lambda Function URL permissions."""

    def test_function_url_has_public_access_permission(self):
        """Test that Function URL has explicit public access permission.

        Lambda Function URLs with auth_type = NONE still need an explicit
        aws_lambda_permission resource for InvokeFunctionUrl.
        """
        lambda_file = AGENTS_SRC / "lambda.tf"
        with open(lambda_file, encoding="utf-8") as f:
            content = f.read()

        # Check if function URL exists
        has_function_url = 'resource "aws_lambda_function_url"' in content
        if has_function_url:
            # Should have permission for InvokeFunctionUrl
            has_invoke_permission = "InvokeFunctionUrl" in content
            assert has_invoke_permission, (
                "Function URL exists but no InvokeFunctionUrl permission found. "
                "Add aws_lambda_permission with function_url_auth_type."
            )
