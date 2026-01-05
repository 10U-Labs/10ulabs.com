"""Layer 1: Contract tests for soc_simulations endpoint.

Tests that local files that must work together are compatible.
No AWS calls. These tests catch contract mismatches between files before deployment.
"""
import re


from repo_utils import REPO_ROOT


SOC_SIMULATIONS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "soc_simulations"


class TestLambdaContracts:
    """Contract tests for Lambda handler and Terraform configuration."""

    def test_lambda_handler_file_exists(self):
        """Verify the Lambda handler file exists."""
        handler_path = SOC_SIMULATIONS_SRC / "lambda" / "handler.py"
        file_exists = handler_path.exists()
        assert file_exists, f"Handler file not found: {handler_path}"

    def test_lambda_handler_defines_handler_function(self):
        """Verify the Lambda handler file defines a handler function."""
        handler_path = SOC_SIMULATIONS_SRC / "lambda" / "handler.py"
        content = handler_path.read_text()
        has_handler = "def handler(" in content
        assert has_handler, "Handler file must define 'def handler(' function"

    def test_lambda_tf_references_handler_correctly(self):
        """Verify lambda.tf references handler.handler."""
        lambda_tf = SOC_SIMULATIONS_SRC / "lambda.tf"
        content = lambda_tf.read_text()
        has_handler_ref = 'handler = "handler.handler"' in content
        assert has_handler_ref, "lambda.tf must reference handler = 'handler.handler'"


class TestTerraformContracts:
    """Contract tests for Terraform configuration files."""

    def test_backend_tf_exists(self):
        """Verify backend.tf exists."""
        backend_path = SOC_SIMULATIONS_SRC / "backend.tf"
        file_exists = backend_path.exists()
        assert file_exists, f"backend.tf not found: {backend_path}"

    def test_backend_tf_has_s3_backend(self):
        """Verify backend.tf configures S3 backend."""
        backend_path = SOC_SIMULATIONS_SRC / "backend.tf"
        content = backend_path.read_text()
        has_s3_backend = 'backend "s3"' in content
        assert has_s3_backend, "backend.tf must configure S3 backend"

    def test_backend_tf_has_state_key(self):
        """Verify backend.tf has a key for state file."""
        backend_path = SOC_SIMULATIONS_SRC / "backend.tf"
        content = backend_path.read_text()
        has_key = re.search(r'key\s*=\s*"[^"]+"', content)
        assert has_key, "backend.tf must have a key configuration"

    def test_providers_tf_exists(self):
        """Verify providers.tf exists."""
        providers_path = SOC_SIMULATIONS_SRC / "providers.tf"
        file_exists = providers_path.exists()
        assert file_exists, f"providers.tf not found: {providers_path}"

    def test_providers_tf_has_aws_provider(self):
        """Verify providers.tf configures AWS provider."""
        providers_path = SOC_SIMULATIONS_SRC / "providers.tf"
        content = providers_path.read_text()
        has_aws_provider = 'provider "aws"' in content
        assert has_aws_provider, "providers.tf must configure AWS provider"

    def test_shared_tf_references_common_module(self):
        """Verify shared.tf references the common module."""
        shared_path = SOC_SIMULATIONS_SRC / "shared.tf"
        content = shared_path.read_text()
        has_common_ref = 'module "common"' in content
        assert has_common_ref, "shared.tf must reference module 'common'"

    def test_shared_tf_references_api_remote_state(self):
        """Verify shared.tf references API common routing remote state."""
        shared_path = SOC_SIMULATIONS_SRC / "shared.tf"
        content = shared_path.read_text()
        has_api_state = 'api_common_routing' in content
        assert has_api_state, "shared.tf must reference api_common_routing remote state"

    def test_iam_tf_exists(self):
        """Verify iam.tf exists."""
        iam_path = SOC_SIMULATIONS_SRC / "iam.tf"
        file_exists = iam_path.exists()
        assert file_exists, f"iam.tf not found: {iam_path}"

    def test_locals_tf_exists(self):
        """Verify locals.tf exists."""
        locals_path = SOC_SIMULATIONS_SRC / "locals.tf"
        file_exists = locals_path.exists()
        assert file_exists, f"locals.tf not found: {locals_path}"


class TestOutputContracts:
    """Contract tests for Terraform outputs."""

    def test_outputs_tf_exists(self):
        """Verify outputs.tf exists."""
        outputs_path = SOC_SIMULATIONS_SRC / "outputs.tf"
        file_exists = outputs_path.exists()
        assert file_exists, f"outputs.tf not found: {outputs_path}"

    def test_outputs_tf_exports_lambda_function_name(self):
        """Verify outputs.tf exports lambda_function_name."""
        outputs_path = SOC_SIMULATIONS_SRC / "outputs.tf"
        content = outputs_path.read_text()
        has_function_name = 'lambda_function_name' in content
        assert has_function_name, "outputs.tf must export lambda_function_name"

    def test_outputs_tf_exports_log_group_name(self):
        """Verify outputs.tf exports log_group_name."""
        outputs_path = SOC_SIMULATIONS_SRC / "outputs.tf"
        content = outputs_path.read_text()
        has_log_group = 'log_group_name' in content
        assert has_log_group, "outputs.tf must export log_group_name"
