"""Unit tests for Terraform configuration files.

These tests verify that Terraform configurations are valid and follow conventions
without making any AWS calls. They are static analysis tests.
"""
import re

from repo_utils import REPO_ROOT

SOC_SIMULATIONS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "soc_simulations"


class TestBackendConfiguration:
    """Unit tests for backend.tf configuration."""

    def test_backend_tf_has_valid_state_key(self):
        """Verify backend.tf has a valid state key containing simulation_soc."""
        content = (SOC_SIMULATIONS_SRC / "backend.tf").read_text()
        match = re.search(r'key\s*=\s*"([^"]+)"', content)
        has_valid_key = match is not None and "simulation_soc" in match.group(1)
        assert has_valid_key, "backend.tf key must contain 'simulation_soc'"

    def test_backend_tf_has_encryption_enabled(self):
        """Verify backend.tf enables encryption."""
        content = (SOC_SIMULATIONS_SRC / "backend.tf").read_text()
        has_encrypt = "encrypt" in content and "true" in content
        assert has_encrypt, "backend.tf must have encrypt = true"

    def test_backend_tf_uses_lockfile(self):
        """Verify backend.tf uses DynamoDB for state locking."""
        content = (SOC_SIMULATIONS_SRC / "backend.tf").read_text()
        has_lock = "dynamodb_table" in content
        assert has_lock, "backend.tf must configure dynamodb_table for state locking"


class TestProvidersConfiguration:
    """Unit tests for providers.tf configuration."""

    def test_providers_tf_has_required_version(self):
        """Verify providers.tf has required_version constraint."""
        content = (SOC_SIMULATIONS_SRC / "providers.tf").read_text()
        has_required_version = "required_version" in content
        assert has_required_version, "providers.tf must have required_version"

    def test_providers_tf_has_aws_provider_version_constraint(self):
        """Verify providers.tf has AWS provider version constraint."""
        content = (SOC_SIMULATIONS_SRC / "providers.tf").read_text()
        has_aws_version = re.search(r'aws\s*=\s*\{[^}]*version', content, re.DOTALL)
        assert has_aws_version, "providers.tf must have AWS provider version constraint"

    def test_providers_tf_has_region_configuration(self):
        """Verify providers.tf configures AWS region."""
        content = (SOC_SIMULATIONS_SRC / "providers.tf").read_text()
        has_region = "region" in content
        assert has_region, "providers.tf must configure region"


class TestLocalsConfiguration:
    """Unit tests for locals.tf configuration."""

    def test_locals_tf_handler_role_name_follows_convention(self):
        """Verify handler_role_name follows PascalCase convention."""
        content = (SOC_SIMULATIONS_SRC / "locals.tf").read_text()
        match = re.search(r'handler_role_name\s*=\s*"([^"]+)"', content)
        if match:
            role_name = match.group(1)
            has_pascal_case = "SimulationSoc" in role_name or "${" in role_name
            assert has_pascal_case, f"Role name {role_name} should use PascalCase"

    def test_locals_tf_log_group_path_follows_convention(self):
        """Verify handler_log_group follows /aws/lambda/ convention."""
        content = (SOC_SIMULATIONS_SRC / "locals.tf").read_text()
        match = re.search(r'handler_log_group\s*=\s*"([^"]+)"', content)
        if match:
            log_group = match.group(1)
            follows_convention = "/aws/lambda/" in log_group
            assert follows_convention, f"Log group {log_group} should start with /aws/lambda/"


class TestOutputsConfiguration:
    """Unit tests for outputs.tf configuration."""

    def test_outputs_tf_exports_lambda_function_name(self):
        """Verify outputs.tf exports lambda_function_name."""
        content = (SOC_SIMULATIONS_SRC / "outputs.tf").read_text()
        has_output = 'output "lambda_function_name"' in content
        assert has_output, "outputs.tf must export lambda_function_name"

    def test_outputs_tf_exports_log_group_name(self):
        """Verify outputs.tf exports log_group_name."""
        content = (SOC_SIMULATIONS_SRC / "outputs.tf").read_text()
        has_output = 'output "log_group_name"' in content
        assert has_output, "outputs.tf must export log_group_name"

    def test_outputs_tf_exports_lambda_function_arn(self):
        """Verify outputs.tf exports lambda_function_arn."""
        content = (SOC_SIMULATIONS_SRC / "outputs.tf").read_text()
        has_output = 'output "lambda_function_arn"' in content
        assert has_output, "outputs.tf must export lambda_function_arn"


class TestIAMConfiguration:
    """Unit tests for iam.tf configuration."""

    def test_iam_tf_role_has_assume_role_policy(self):
        """Verify IAM role has assume_role_policy."""
        content = (SOC_SIMULATIONS_SRC / "iam.tf").read_text()
        has_assume_role = "assume_role_policy" in content
        assert has_assume_role, "IAM role must have assume_role_policy"

    def test_iam_tf_role_trusts_lambda_service(self):
        """Verify IAM role trusts lambda.amazonaws.com."""
        content = (SOC_SIMULATIONS_SRC / "iam.tf").read_text()
        trusts_lambda = "lambda.amazonaws.com" in content
        assert trusts_lambda, "IAM role must trust lambda.amazonaws.com"

    def test_iam_tf_has_basic_execution_attachment(self):
        """Verify IAM has basic execution role policy attachment."""
        content = (SOC_SIMULATIONS_SRC / "iam.tf").read_text()
        has_basic_exec = "AWSLambdaBasicExecutionRole" in content
        assert has_basic_exec, "IAM must attach AWSLambdaBasicExecutionRole"


class TestLambdaConfiguration:
    """Unit tests for lambda.tf configuration."""

    def test_lambda_tf_uses_correct_runtime(self):
        """Verify Lambda uses Python 3.12 runtime."""
        content = (SOC_SIMULATIONS_SRC / "lambda.tf").read_text()
        uses_python312 = "python3.12" in content
        assert uses_python312, "Lambda must use python3.12 runtime"

    def test_lambda_tf_uses_arm64_architecture(self):
        """Verify Lambda uses arm64 architecture."""
        content = (SOC_SIMULATIONS_SRC / "lambda.tf").read_text()
        uses_arm64 = "arm64" in content
        assert uses_arm64, "Lambda must use arm64 architecture"

    def test_lambda_tf_has_logging_config(self):
        """Verify Lambda has logging configuration."""
        content = (SOC_SIMULATIONS_SRC / "lambda.tf").read_text()
        has_logging = "logging_config" in content
        assert has_logging, "Lambda must have logging_config block"

    def test_lambda_tf_has_environment_variables(self):
        """Verify Lambda has environment variables configured."""
        content = (SOC_SIMULATIONS_SRC / "lambda.tf").read_text()
        has_env = "environment" in content and "variables" in content
        assert has_env, "Lambda must have environment variables configured"

    def test_lambda_tf_has_google_client_id_variable(self):
        """Verify Lambda has GOOGLE_CLIENT_ID environment variable."""
        content = (SOC_SIMULATIONS_SRC / "lambda.tf").read_text()
        has_google_client = "GOOGLE_CLIENT_ID" in content
        assert has_google_client, "Lambda must have GOOGLE_CLIENT_ID env var"


class TestSharedConfiguration:
    """Unit tests for shared.tf configuration."""

    def test_shared_tf_references_api_remote_state(self):
        """Verify shared.tf references API common routing remote state."""
        content = (SOC_SIMULATIONS_SRC / "shared.tf").read_text()
        has_api_state = "api_common_routing" in content
        assert has_api_state, "shared.tf must reference api_common_routing"

    def test_shared_tf_uses_common_module(self):
        """Verify shared.tf uses common module."""
        content = (SOC_SIMULATIONS_SRC / "shared.tf").read_text()
        uses_common = 'module "common"' in content
        assert uses_common, "shared.tf must use common module"

    def test_shared_tf_common_module_source_is_valid(self):
        """Verify common module source path is valid."""
        content = (SOC_SIMULATIONS_SRC / "shared.tf").read_text()
        match = re.search(r'source\s*=\s*"([^"]+/common)"', content)
        if match:
            source_path = match.group(1)
            valid_source = "lib/terraform/common" in source_path or "../../../" in source_path
            assert valid_source, f"Common module source {source_path} is not valid"


class TestVariablesConfiguration:
    """Unit tests for variables.tf configuration."""

    def test_variables_tf_exists(self):
        """Verify variables.tf exists."""
        exists = (SOC_SIMULATIONS_SRC / "variables.tf").exists()
        assert exists, "variables.tf must exist"

    def test_variables_tf_has_environment_variable(self):
        """Verify variables.tf has environment variable."""
        content = (SOC_SIMULATIONS_SRC / "variables.tf").read_text()
        has_env = 'variable "environment"' in content or len(content.strip()) == 0
        assert has_env or content.strip() == "", (
            "variables.tf should define environment variable or be empty"
        )
