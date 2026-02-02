"""Pre-deployment integration tests for drift recoveries Terraform config."""
from pathlib import Path

from test_utils.terraform_assertions import (
    get_missing_terraform_files,
    lambda_handler_exists,
    DEFAULT_TERRAFORM_FILES,
)


# Drift recoveries requires additional files beyond defaults
DRIFT_RECOVERIES_EXTRA_FILES = [
    "eventbridge.tf",
    "sns.tf",
    "data.tf",
]
DRIFT_RECOVERIES_FILES = DEFAULT_TERRAFORM_FILES + DRIFT_RECOVERIES_EXTRA_FILES


class TestDriftRecoveriesTerraformFiles:
    """Tests that drift recoveries Terraform files exist."""

    def test_all_required_terraform_files_exist(self, terraform_dir: Path):
        """All required Terraform configuration files exist."""
        assert get_missing_terraform_files(terraform_dir, DRIFT_RECOVERIES_FILES) == []

    def test_lambda_handler_file_exists(self, terraform_dir: Path):
        """Lambda handler Python file exists in lambda subdirectory."""
        assert lambda_handler_exists(terraform_dir)
