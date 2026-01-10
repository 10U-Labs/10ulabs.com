"""Layer 1: Contract tests.

Verify local files that must work together are compatible.
"""
import ast
import re

import pytest
from repo_utils import REPO_ROOT


ENDPOINT_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ecs" / "images"
HANDLER_PATH = ENDPOINT_DIR / "lambda" / "handler.py"
LAMBDA_TF_PATH = ENDPOINT_DIR / "lambda.tf"
LAMBDA_HTTP_PATH = REPO_ROOT / "lib" / "python" / "lambda_http" / "__init__.py"


class TestHandlerFileContract:
    """Verify handler file exists where Terraform expects it."""

    def test_handler_file_exists(self):
        """Verify lambda/handler.py exists at expected path."""
        assert HANDLER_PATH.exists(), (
            f"Handler file not found at {HANDLER_PATH}. "
            "Terraform lambda.tf references this file."
        )

    def test_handler_file_is_valid_python(self):
        """Verify handler.py is valid Python syntax."""
        content = HANDLER_PATH.read_text()
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"Handler file has syntax error: {e}")


class TestHandlerExportsContract:
    """Verify handler exports what Terraform references."""

    def test_handler_exports_lambda_handler(self):
        """Verify handler.py exports lambda_handler function."""
        content = HANDLER_PATH.read_text()
        tree = ast.parse(content)

        function_names = [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]

        assert "lambda_handler" in function_names, (
            "Handler file must export 'lambda_handler' function. "
            "Terraform lambda.tf references handler='handler.lambda_handler'"
        )


class TestEnvironmentVariablesContract:
    """Verify environment variables match between handler and Terraform."""

    @pytest.fixture
    def handler_env_vars(self):
        """Extract environment variable names used by handler."""
        content = HANDLER_PATH.read_text()
        # Match os.environ['VAR_NAME'] or os.environ.get('VAR_NAME')
        pattern = r"os\.environ(?:\[|\.get\()[\'\"](\w+)[\'\"]"
        return set(re.findall(pattern, content))

    @pytest.fixture
    def terraform_env_vars(self):
        """Extract environment variable names provided by Terraform."""
        content = LAMBDA_TF_PATH.read_text()
        # Match variable names in environment block
        # Pattern: VAR_NAME = value (with possible whitespace)
        env_block_match = re.search(
            r"environment\s*\{[^}]*variables\s*=\s*\{([^}]+)\}",
            content,
            re.DOTALL
        )
        if not env_block_match:
            return set()

        env_block = env_block_match.group(1)
        # Extract variable names (left side of =)
        pattern = r"^\s*(\w+)\s*="
        return set(re.findall(pattern, env_block, re.MULTILINE))

    def test_handler_env_vars_provided_by_terraform(
        self, handler_env_vars, terraform_env_vars
    ):
        """Verify all environment variables used by handler are provided by Terraform."""
        missing = handler_env_vars - terraform_env_vars
        assert not missing, (
            f"Handler uses environment variables not provided by Terraform: {missing}. "
            f"Handler uses: {handler_env_vars}. "
            f"Terraform provides: {terraform_env_vars}"
        )

    def test_terraform_provides_ecr_repository(self, terraform_env_vars):
        """Verify Terraform provides ECR_REPOSITORY."""
        assert "ECR_REPOSITORY" in terraform_env_vars

    def test_terraform_provides_github_repo(self, terraform_env_vars):
        """Verify Terraform provides GITHUB_REPO."""
        assert "GITHUB_REPO" in terraform_env_vars

    def test_terraform_provides_github_token_secret_name(self, terraform_env_vars):
        """Verify Terraform provides GITHUB_TOKEN_SECRET_NAME."""
        assert "GITHUB_TOKEN_SECRET_NAME" in terraform_env_vars


class TestLambdaHttpLibraryContract:
    """Verify lambda_http library exists where Terraform expects it."""

    def test_lambda_http_library_exists(self):
        """Verify lambda_http/__init__.py exists at expected path."""
        assert LAMBDA_HTTP_PATH.exists(), (
            f"lambda_http library not found at {LAMBDA_HTTP_PATH}. "
            "Terraform lambda.tf includes this file in the Lambda package."
        )

    def test_lambda_http_path_matches_terraform(self):
        """Verify lambda_http path in Terraform matches actual location."""
        content = LAMBDA_TF_PATH.read_text()
        # Terraform uses relative path from lambda.tf
        assert "lib/python/lambda_http/__init__.py" in content, (
            "Terraform lambda.tf should reference lib/python/lambda_http/__init__.py"
        )
