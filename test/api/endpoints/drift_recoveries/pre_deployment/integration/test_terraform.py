"""Pre-deployment integration tests for drift recoveries Terraform config."""
from pathlib import Path

from test_utils.terraform_assertions import (
    get_missing_terraform_files,
    lambda_handler_exists,
)


# Drift recoveries required Terraform files
DRIFT_RECOVERIES_FILES = [
    "backend.tf",
    "providers.tf",
    "shared.tf",
    "locals.tf",
    "lambda.tf",
    "iam.tf",
    "eventbridge.tf",
    "sns.tf",
    "data.tf",
    "outputs.tf",
]


class TestDriftRecoveriesTerraformFiles:
    """Tests that drift recoveries Terraform files exist."""

    def test_all_required_terraform_files_exist(self, terraform_dir: Path):
        """All required Terraform configuration files exist."""
        assert get_missing_terraform_files(terraform_dir, DRIFT_RECOVERIES_FILES) == []

    def test_lambda_handler_file_exists(self, terraform_dir: Path):
        """Lambda handler Python file exists in lambda subdirectory."""
        assert lambda_handler_exists(terraform_dir)
