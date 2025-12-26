"""Layer 3: Wiring - Verify components are connected properly.

These tests verify that all components created by terraform apply are
connected properly. Assumes existence (Layer 1) and configuration (Layer 2)
have passed.
"""
import pytest

pytestmark = pytest.mark.layer(3)


class TestLambdaFunctionWiring:
    """Layer 3: Verify Lambda function is wired correctly."""

    def test_lambda_has_iam_role_attached(
        self, fetched_lambda_function, handler_function_name
    ):
        """Verify Lambda function has an IAM role attached."""
        role_arn = fetched_lambda_function['Configuration'].get('Role', '')
        assert role_arn.startswith('arn:aws:iam::'), (
            f"Lambda function '{handler_function_name}' has invalid role ARN: "
            f"{role_arn}"
        )

    def test_lambda_role_exists_in_iam(
        self, fetched_lambda_function, fetched_iam_role, handler_function_name
    ):
        """Verify Lambda function's role exists in IAM."""
        role_arn = fetched_lambda_function['Configuration'].get('Role', '')
        role_name_from_lambda = role_arn.split('/')[-1]
        role_name_from_iam = fetched_iam_role['Role']['RoleName']
        assert role_name_from_lambda == role_name_from_iam, (
            f"Lambda function '{handler_function_name}' role ARN doesn't match "
            f"IAM role: {role_name_from_lambda} != {role_name_from_iam}"
        )
