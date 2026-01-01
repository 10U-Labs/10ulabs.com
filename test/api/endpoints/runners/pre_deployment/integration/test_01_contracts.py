"""Layer 1: Contract tests for runners endpoint pre-deployment validation.

Verify cross-file compatibility:
- Lambda handler exports match Terraform references
- Remote state outputs referenced exist in api_common_routing
"""
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import create_remote_state_contract_tests

pytestmark = pytest.mark.layer(1)

RUNNERS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners"


class TestLambdaHandlerContracts:
    """Verify Lambda handler exports match Terraform references."""

    def test_handler_exports_lambda_handler(self, handler_content: str):
        """Verify handler.py exports lambda_handler function."""
        assert "def lambda_handler(" in handler_content, (
            "handler.py must export lambda_handler function. "
            "This is required by the Lambda configuration in lambda.tf"
        )

    def test_lambda_tf_references_correct_handler(self, lambda_tf_content: str):
        """Verify lambda.tf references handler.lambda_handler."""
        assert 'handler          = "handler.lambda_handler"' in lambda_tf_content, (
            "lambda.tf must set handler to 'handler.lambda_handler'. "
            "This must match the function exported by handler.py"
        )


class TestLambdaPackageContracts:
    """Verify Lambda package includes all required modules."""

    def test_handler_imports_runner_labels(self, handler_content: str):
        """Verify handler imports runner_labels module."""
        assert "import runner_labels" in handler_content, (
            "handler.py must import runner_labels module. "
            "This is bundled as runner_labels.py in the Lambda package."
        )

    def test_lambda_package_includes_runner_labels(self, lambda_tf_content: str):
        """Verify Lambda package includes runner_labels.py."""
        assert 'runner_labels.py' in lambda_tf_content, (
            "lambda.tf must include runner_labels.py in the archive_file. "
            "The handler imports this module."
        )

    def test_lambda_package_includes_runners_json(self, lambda_tf_content: str):
        """Verify Lambda package includes etc/runners.json."""
        assert 'etc/runners.json' in lambda_tf_content, (
            "lambda.tf must include etc/runners.json in the archive_file. "
            "This is required by the runner_labels module."
        )


# Test that remote state outputs referenced in lambda.tf exist in api backend
TestRemoteStateContract = create_remote_state_contract_tests(
    endpoint_src=RUNNERS_SRC,
    endpoint_name="runners",
    lambda_file="lambda.tf",
    required_outputs=["api_gateway_id", "api_key_ssm_parameter"],
)


class TestIAMRemoteStateContracts:
    """Verify IAM references to remote state outputs."""

    def test_iam_tf_exists(self, runners_dir: Path):
        """Verify iam.tf file exists."""
        iam_path = runners_dir / "iam.tf"
        assert iam_path.exists(), f"iam.tf not found at {iam_path}"

    def test_iam_references_api_key_ssm_parameter_arn(self, runners_dir: Path):
        """Verify iam.tf references api_key_ssm_parameter_arn from api backend."""
        iam_path = runners_dir / "iam.tf"
        content = iam_path.read_text()
        assert "api_key_ssm_parameter_arn" in content, (
            "iam.tf must reference data.terraform_remote_state.api.outputs."
            "api_key_ssm_parameter_arn for SSM access policy"
        )
