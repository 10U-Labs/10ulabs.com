"""Shared test helpers for naming convention tests across endpoints."""
import pytest

from naming_conventions import validate_name


def create_iam_role_tests(roles: list):
    """Create test class for IAM role naming conventions.

    Args:
        roles: List of (resource_name, role_name) tuples from extract_iam_role_names()

    Returns:
        Test class with parametrized tests for the given roles.
    """
    class TestIAMRoleNamingConventions:
        """Tests for IAM role naming conventions."""

        @pytest.mark.parametrize(
            "resource_name,role_name",
            roles,
            ids=[f"iam_role_{r[0]}" for r in roles],
        )
        def test_iam_role_name_is_pascalcase(self, resource_name, role_name):
            """Verify IAM role name uses PascalCase (no dashes or underscores)."""
            error = validate_name(role_name)
            assert error is None, (
                f"IAM role '{resource_name}' has invalid name '{role_name}': {error}"
            )

        def test_no_iam_role_names_contain_dashes(self):
            """Verify no IAM role names contain dashes."""
            violations = [(r, n) for r, n in roles if '-' in n]
            assert len(violations) == 0, (
                f"Found {len(violations)} IAM roles with dashes:\n"
                + "\n".join(f"  - {r}: '{n}'" for r, n in violations)
            )

    return TestIAMRoleNamingConventions


def create_lambda_function_tests(functions: list):
    """Create test class for Lambda function naming conventions.

    Args:
        functions: List of (resource_name, function_name) tuples

    Returns:
        Test class with parametrized tests for the given functions.
    """
    class TestLambdaFunctionNamingConventions:
        """Tests for Lambda function naming conventions."""

        @pytest.mark.parametrize(
            "resource_name,function_name",
            functions,
            ids=[f"lambda_{f[0]}" for f in functions],
        )
        def test_lambda_function_name_is_pascalcase(self, resource_name, function_name):
            """Verify Lambda function name uses PascalCase (no dashes or underscores)."""
            error = validate_name(function_name)
            assert error is None, (
                f"Lambda function '{resource_name}' has invalid name "
                f"'{function_name}': {error}"
            )

        def test_no_lambda_function_names_contain_dashes(self):
            """Verify no Lambda function names contain dashes."""
            violations = [(r, n) for r, n in functions if '-' in n]
            assert len(violations) == 0, (
                f"Found {len(violations)} Lambda functions with dashes:\n"
                + "\n".join(f"  - {r}: '{n}'" for r, n in violations)
            )

    return TestLambdaFunctionNamingConventions
