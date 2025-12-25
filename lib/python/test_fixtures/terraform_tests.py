"""Shared test factories for Terraform configuration tests.

Provides factory functions to generate test classes for common Terraform
patterns like backend.tf and outputs.tf verification.
"""
import re
from pathlib import Path
from typing import Optional

import pytest
from naming_conventions import validate_name
from repo_utils import REPO_ROOT
from terraform_config import extract_iam_role_names, extract_lambda_function_names

API_BACKEND_OUTPUTS_FILE = REPO_ROOT / "src" / "api" / "backend" / "outputs.tf"


def get_api_backend_outputs() -> set:
    """Extract all output names from api/backend/outputs.tf."""
    with open(API_BACKEND_OUTPUTS_FILE, encoding="utf-8") as f:
        content = f.read()
    pattern = r'output\s+"(\w+)"'
    return set(re.findall(pattern, content))


def create_backend_terraform_tests(
    endpoint_src: Path,
    state_key: str,
    bucket: str = "10ulabs-terraform-state-us-east-2",
):
    """Create a test class for backend.tf verification.

    Args:
        endpoint_src: Path to the endpoint source directory
        state_key: The expected state file key (e.g., "health/terraform.tfstate")
        bucket: The expected S3 bucket name

    Returns:
        Test class with backend.tf verification tests
    """
    backend_file = endpoint_src / "backend.tf"

    class TestBackendTerraform:
        """Tests for backend.tf Terraform configuration."""

        def test_backend_terraform_file_exists(self):
            """Verify backend.tf file exists."""
            assert backend_file.exists()

        def test_backend_uses_s3(self):
            """Verify S3 backend is configured."""
            with open(backend_file, encoding="utf-8") as f:
                content = f.read()
            assert 'backend "s3"' in content

        def test_backend_uses_correct_bucket(self):
            """Verify correct S3 bucket is used."""
            with open(backend_file, encoding="utf-8") as f:
                content = f.read()
            assert f'bucket       = "{bucket}"' in content

        def test_backend_uses_correct_key(self):
            """Verify correct state file key is used."""
            with open(backend_file, encoding="utf-8") as f:
                content = f.read()
            assert f'key          = "{state_key}"' in content

        def test_backend_uses_encryption(self):
            """Verify state file encryption is enabled."""
            with open(backend_file, encoding="utf-8") as f:
                content = f.read()
            assert 'encrypt      = true' in content

        def test_backend_uses_lockfile(self):
            """Verify state locking is enabled."""
            with open(backend_file, encoding="utf-8") as f:
                content = f.read()
            assert 'use_lockfile = true' in content

        def test_backend_requires_terraform_version(self):
            """Verify Terraform version requirement."""
            with open(backend_file, encoding="utf-8") as f:
                content = f.read()
            assert 'required_version = ">= 1.14"' in content

        def test_backend_requires_archive_provider(self):
            """Verify archive provider requirement."""
            with open(backend_file, encoding="utf-8") as f:
                content = f.read()
            assert 'hashicorp/archive' in content

        def test_backend_requires_aws_provider(self):
            """Verify AWS provider requirement."""
            with open(backend_file, encoding="utf-8") as f:
                content = f.read()
            assert 'hashicorp/aws' in content

    return TestBackendTerraform


def create_outputs_terraform_tests(
    endpoint_src: Path,
    required_outputs: Optional[list] = None,
):
    """Create a test class for outputs.tf verification.

    Args:
        endpoint_src: Path to the endpoint source directory
        required_outputs: List of required output names (without 'output "' prefix)
                         Defaults to lambda_function_arn, lambda_function_name

    Returns:
        Test class with outputs.tf verification tests
    """
    if required_outputs is None:
        required_outputs = ["lambda_function_arn", "lambda_function_name"]

    outputs_file = endpoint_src / "outputs.tf"

    class TestOutputsTerraform:
        """Tests for outputs.tf Terraform configuration."""

        def test_outputs_terraform_file_exists(self):
            """Verify outputs.tf file exists."""
            assert outputs_file.exists()

        def test_outputs_file_is_valid_terraform(self):
            """Verify outputs.tf is valid Terraform syntax."""
            with open(outputs_file, encoding="utf-8") as f:
                content = f.read()
            # Basic check for Terraform output block syntax
            assert 'output "' in content or len(content.strip()) == 0, (
                "outputs.tf exists but contains no output blocks"
            )

    # Dynamically add test methods for each required output
    for output_name in required_outputs:

        def make_test(name):
            def test_output_exists(_self):
                with open(outputs_file, encoding="utf-8") as f:
                    content = f.read()
                assert f'output "{name}"' in content

            return test_output_exists

        test_method = make_test(output_name)
        test_method.__name__ = f"test_{output_name}_output_exists"
        test_method.__doc__ = f"Verify {output_name} output is defined."
        setattr(TestOutputsTerraform, test_method.__name__, test_method)

    return TestOutputsTerraform


def create_remote_state_contract_tests(
    endpoint_src: Path,
    endpoint_name: str,
    lambda_file: str = "lambda.tf",
    required_outputs: Optional[list] = None,
):
    """Create a test class for remote state contract verification.

    Verifies that terraform_remote_state.api.outputs references in the
    endpoint's lambda.tf exist in api/backend/outputs.tf.

    Args:
        endpoint_src: Path to the endpoint source directory
        endpoint_name: Name of the endpoint (for error messages)
        lambda_file: Name of the lambda file to check (default: lambda.tf)
        required_outputs: List of backend outputs that must exist

    Returns:
        Test class with remote state contract verification tests
    """
    lambda_path = endpoint_src / lambda_file

    def get_api_remote_state_references():
        """Extract all data.terraform_remote_state.api.outputs.X references."""
        with open(lambda_path, encoding="utf-8") as f:
            content = f.read()
        pattern = r'data\.terraform_remote_state\.api\.outputs\.(\w+)'
        return set(re.findall(pattern, content))

    class TestRemoteStateContract:
        """Tests for remote state output contract between endpoint and api backend."""

        def test_all_api_remote_state_references_exist_in_backend_outputs(self):
            """Verify all api remote state references exist in backend outputs."""
            references = get_api_remote_state_references()
            outputs = get_api_backend_outputs()
            missing = references - outputs

            assert not missing, (
                f"{endpoint_name}/{lambda_file} references api backend outputs that "
                f"don't exist: {missing}. Add these outputs to src/api/backend/outputs.tf"
            )

        def test_lambda_file_exists(self):
            """Verify the lambda file exists for remote state analysis."""
            assert lambda_path.exists(), f"{lambda_file} does not exist in endpoint"

    # Dynamically add test methods for each required output
    if required_outputs:
        for output_name in required_outputs:

            def make_test(name):
                def test_output_exists(_self):
                    outputs = get_api_backend_outputs()
                    assert name in outputs, (
                        f"{name} output missing from api/backend/outputs.tf. "
                        f"This is required by the {endpoint_name} endpoint."
                    )

                return test_output_exists

            test_method = make_test(output_name)
            test_method.__name__ = f"test_{output_name}_output_exists_in_backend"
            test_method.__doc__ = f"Verify {output_name} output exists in api backend."
            setattr(TestRemoteStateContract, test_method.__name__, test_method)

    return TestRemoteStateContract


def create_naming_conventions_tests(
    endpoint_src: Path,
    iam_file: str = "iam.tf",
    lambda_file: str = "lambda.tf",
    use_handler_names: bool = False,
):
    """Create test classes for IAM role and Lambda function naming conventions.

    Args:
        endpoint_src: Path to the endpoint source directory
        iam_file: Name of the IAM Terraform file
        lambda_file: Name of the Lambda Terraform file
        use_handler_names: Whether to use handler names for Lambda functions

    Returns:
        Tuple of (TestIAMRoleNamingConventions, TestLambdaFunctionNamingConventions)
    """
    iam_path = endpoint_src / iam_file
    lambda_path = endpoint_src / lambda_file

    iam_roles = extract_iam_role_names(iam_path)
    lambda_functions = extract_lambda_function_names(
        lambda_path, use_handler_names=use_handler_names
    )

    class TestIAMRoleNamingConventions:
        """Tests for IAM role naming conventions."""

        @pytest.mark.parametrize(
            "resource_name,role_name",
            iam_roles if iam_roles else [("NONE", "NONE")],
            ids=[f"iam_role_{r[0]}" for r in iam_roles] if iam_roles else ["no_roles_found"],
        )
        def test_iam_role_name_is_pascalcase(self, resource_name, role_name):
            """Verify IAM role name uses PascalCase (no dashes or underscores)."""
            if resource_name == "NONE":
                pytest.fail("No IAM roles found in iam.tf - check Terraform files")
            error = validate_name(role_name)
            assert error is None, (
                f"IAM role '{resource_name}' has invalid name '{role_name}': {error}"
            )

        def test_no_iam_role_names_contain_dashes(self):
            """Verify no IAM role names contain dashes."""
            violations = [(r, n) for r, n in iam_roles if '-' in n]
            assert len(violations) == 0, (
                f"Found {len(violations)} IAM roles with dashes:\n"
                + "\n".join(f"  - {r}: '{n}'" for r, n in violations)
            )

    class TestLambdaFunctionNamingConventions:
        """Tests for Lambda function naming conventions."""

        @pytest.mark.parametrize(
            "resource_name,function_name",
            lambda_functions if lambda_functions else [("NONE", "NONE")],
            ids=([f"lambda_{f[0]}" for f in lambda_functions]
                 if lambda_functions else ["no_functions_found"]),
        )
        def test_lambda_function_name_is_pascalcase(self, resource_name, function_name):
            """Verify Lambda function name uses PascalCase (no dashes or underscores)."""
            if resource_name == "NONE":
                pytest.fail("No Lambda functions found - check Terraform files")
            error = validate_name(function_name)
            assert error is None, (
                f"Lambda function '{resource_name}' has invalid name "
                f"'{function_name}': {error}"
            )

        def test_no_lambda_function_names_contain_dashes(self):
            """Verify no Lambda function names contain dashes."""
            violations = [(r, n) for r, n in lambda_functions if '-' in n]
            assert len(violations) == 0, (
                f"Found {len(violations)} Lambda functions with dashes:\n"
                + "\n".join(f"  - {r}: '{n}'" for r, n in violations)
            )

    return TestIAMRoleNamingConventions, TestLambdaFunctionNamingConventions
