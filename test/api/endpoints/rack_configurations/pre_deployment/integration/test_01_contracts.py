"""Layer 1: Contract tests for rack_configurations endpoint pre-deployment.

Tests that local files that must work together are compatible.
No AWS calls - just verifies cross-file configuration consistency.

Seven-layer testing model:
- Layer 1: Contracts - Local files are compatible
"""
import re

from repo_utils import REPO_ROOT


RACK_CONFIGURATIONS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "rack_configurations"
HANDLER_PATH = RACK_CONFIGURATIONS_SRC / "lambdas" / "handler.py"
LAMBDA_TF_PATH = RACK_CONFIGURATIONS_SRC / "lambda.tf"


class TestLambdaHandlerContracts:
    """Layer 1: Verify Lambda handler contracts are satisfied."""

    def test_lambda_tf_references_correct_handler_function(self):
        """Verify lambda.tf references the function exported by handler.py."""
        with open(HANDLER_PATH, encoding="utf-8") as f:
            handler_content = f.read()
        with open(LAMBDA_TF_PATH, encoding="utf-8") as f:
            tf_content = f.read()

        # Extract handler reference from lambda.tf (handler = "handler.lambda_handler")
        handler_match = re.search(r'handler\s*=\s*"([^"]+)"', tf_content)
        assert handler_match, "handler attribute not found in lambda.tf"

        tf_handler_ref = handler_match.group(1)
        # handler.lambda_handler means file "handler.py" with function "lambda_handler"
        expected_function = tf_handler_ref.split(".")[-1]

        # Verify handler.py exports the expected function
        assert f"def {expected_function}(" in handler_content, (
            f"handler.py does not export function '{expected_function}' "
            f"referenced in lambda.tf"
        )

    def test_environment_variable_names_match(self):
        """Verify environment variable names in lambda.tf match handler.py usage."""
        with open(HANDLER_PATH, encoding="utf-8") as f:
            handler_content = f.read()
        with open(LAMBDA_TF_PATH, encoding="utf-8") as f:
            tf_content = f.read()

        # Extract environment variable names used in handler.py
        handler_env_vars = set(re.findall(
            r"os\.environ\[['\"](\w+)['\"]\]", handler_content
        ))

        # Extract environment variable names defined in lambda.tf
        # Look for environment { variables { KEY = value } } blocks
        env_block = re.search(
            r"environment\s*\{[^}]*variables\s*=\s*\{([^}]+)\}", tf_content, re.DOTALL
        )
        tf_env_vars = set()
        if env_block:
            tf_env_vars = set(re.findall(r"(\w+)\s*=", env_block.group(1)))

        # Verify all handler env vars are defined in terraform
        missing_vars = handler_env_vars - tf_env_vars
        assert not missing_vars, (
            f"handler.py uses environment variables not defined in lambda.tf: "
            f"{missing_vars}"
        )


class TestTerraformModuleContracts:
    """Layer 1: Verify Terraform module contracts are satisfied."""

    def test_shared_module_reference_valid(self):
        """Verify shared.tf references an existing module."""
        shared_tf_path = RACK_CONFIGURATIONS_SRC / "shared.tf"
        with open(shared_tf_path, encoding="utf-8") as f:
            content = f.read()

        # Verify module reference exists
        module_match = re.search(r'module\s+"(\w+)"\s*\{', content)
        assert module_match, "shared.tf should reference a module"

        # Verify source path is specified
        source_match = re.search(r'source\s*=\s*"([^"]+)"', content)
        assert source_match, "module in shared.tf should have a source"

        # Verify the source path exists
        source_path = source_match.group(1)
        resolved_path = (RACK_CONFIGURATIONS_SRC / source_path).resolve()
        assert resolved_path.exists(), (
            f"Module source path does not exist: {source_path}"
        )

    def test_locals_tf_uses_module_common_outputs(self):
        """Verify locals.tf references outputs from module.common."""
        locals_tf_path = RACK_CONFIGURATIONS_SRC / "locals.tf"
        with open(locals_tf_path, encoding="utf-8") as f:
            content = f.read()

        # Verify locals.tf uses module.common references
        assert "module.common" in content, (
            "locals.tf should reference module.common for shared configuration"
        )
