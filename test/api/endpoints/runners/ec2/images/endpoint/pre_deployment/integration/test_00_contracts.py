"""Layer 0: Contracts - Verify local files are compatible.

These tests verify that files that must work together are compatible.
No AWS calls are made. This layer catches contract mismatches before deployment.
"""
import ast
import re
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


ENDPOINT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ec2" / "images"
HANDLER_PATH = ENDPOINT_SRC / "lambda" / "handler.py"
LAMBDA_TF_PATH = ENDPOINT_SRC / "lambda.tf"


def _get_handler_env_vars() -> set:
    """Extract environment variable names used in handler.py via os.environ[...]."""
    content = HANDLER_PATH.read_text()
    # Match os.environ['VAR_NAME'] or os.environ["VAR_NAME"]
    pattern = r"os\.environ\[['\"]([^'\"]+)['\"]\]"
    return set(re.findall(pattern, content))


def _get_terraform_env_vars() -> set:
    """Extract environment variable names set in lambda.tf."""
    content = LAMBDA_TF_PATH.read_text()
    # Match variable names in the environment block
    # Pattern: VAR_NAME = ... (inside environment { variables = { ... } })
    env_block_match = re.search(
        r'environment\s*\{\s*variables\s*=\s*\{([^}]+)\}',
        content,
        re.DOTALL
    )
    if not env_block_match:
        return set()
    env_block = env_block_match.group(1)
    # Extract variable names (left side of = sign)
    return set(re.findall(r'^\s*(\w+)\s*=', env_block, re.MULTILINE))


def _get_handler_exports() -> set:
    """Extract top-level function names exported by handler.py."""
    content = HANDLER_PATH.read_text()
    tree = ast.parse(content)
    return {
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_')
    }


def _get_terraform_handler_reference() -> str:
    """Extract the handler reference from lambda.tf."""
    content = LAMBDA_TF_PATH.read_text()
    match = re.search(r'handler\s*=\s*"([^"]+)"', content)
    return match.group(1) if match else ""


class TestLambdaHandlerContract:
    """Verify Lambda handler exports match Terraform references."""

    def test_handler_function_exists(self):
        """Verify handler.py exports the function Terraform expects."""
        exports = _get_handler_exports()
        tf_handler = _get_terraform_handler_reference()
        # Terraform uses "handler.lambda_handler" - extract function name
        expected_function = tf_handler.split('.')[-1] if tf_handler else ""
        assert expected_function in exports, (
            f"Terraform references '{tf_handler}' but handler.py exports: {exports}"
        )

    def test_handler_reference_has_dot_separator(self):
        """Verify Terraform handler reference uses module.function format."""
        tf_handler = _get_terraform_handler_reference()
        assert '.' in tf_handler, (
            f"Terraform handler reference '{tf_handler}' should be 'module.function'"
        )

    def test_handler_reference_uses_handler_module(self):
        """Verify Terraform handler reference uses 'handler' module."""
        tf_handler = _get_terraform_handler_reference()
        module = tf_handler.rsplit('.', 1)[0] if '.' in tf_handler else ""
        assert module == "handler", (
            f"Handler module should be 'handler', got '{module}'"
        )


class TestEnvironmentVariableContract:
    """Verify environment variables match between Terraform and handler."""

    # AWS_REGION is provided by Lambda runtime, not Terraform
    RUNTIME_PROVIDED_VARS = {'AWS_REGION'}

    def test_all_handler_vars_provided_by_terraform_or_runtime(self):
        """Verify all env vars used by handler are provided."""
        handler_vars = _get_handler_env_vars()
        terraform_vars = _get_terraform_env_vars()
        all_provided = terraform_vars | self.RUNTIME_PROVIDED_VARS
        missing = handler_vars - all_provided
        assert not missing, (
            f"Handler uses env vars not provided by Terraform or runtime: {missing}\n"
            f"Handler uses: {handler_vars}\n"
            f"Terraform provides: {terraform_vars}\n"
            f"Runtime provides: {self.RUNTIME_PROVIDED_VARS}"
        )

    def test_no_unused_terraform_vars(self):
        """Verify Terraform doesn't set unused environment variables."""
        handler_vars = _get_handler_env_vars()
        terraform_vars = _get_terraform_env_vars()
        unused = terraform_vars - handler_vars
        assert not unused, (
            f"Terraform sets env vars not used by handler: {unused}\n"
            f"Terraform provides: {terraform_vars}\n"
            f"Handler uses: {handler_vars}"
        )


class TestLambdaPackageContract:
    """Verify Lambda package includes required dependencies."""

    def test_lambda_http_included_in_package(self):
        """Verify lambda_http module is included in Lambda package."""
        content = LAMBDA_TF_PATH.read_text()
        assert 'lambda_http' in content, (
            "Lambda package should include lambda_http module"
        )

    def test_handler_imports_lambda_http(self):
        """Verify handler.py imports lambda_http."""
        content = HANDLER_PATH.read_text()
        assert 'from lambda_http import' in content or 'import lambda_http' in content, (
            "handler.py should import lambda_http module"
        )
