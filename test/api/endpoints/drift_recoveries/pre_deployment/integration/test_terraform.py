"""Pre-deployment integration tests for drift recoveries Terraform config."""
from pathlib import Path

import pytest

from test_utils.terraform_assertions import (
    get_missing_terraform_files,
    lambda_handler_exists,
    DEFAULT_TERRAFORM_FILES,
)


# Drift recoveries requires config.tf in addition to standard files
DRIFT_RECOVERIES_EXTRA_FILES = ["config.tf"]
DRIFT_RECOVERIES_ALL_FILES = DEFAULT_TERRAFORM_FILES + DRIFT_RECOVERIES_EXTRA_FILES


class TestDriftRecoveriesTerraformFiles:
    """Tests that drift recoveries Terraform files exist."""

    def test_all_required_terraform_files_exist(self, terraform_dir: Path):
        """All required Terraform configuration files exist."""
        assert get_missing_terraform_files(terraform_dir, DRIFT_RECOVERIES_ALL_FILES) == []

    def test_lambda_handler_file_exists(self, terraform_dir: Path):
        """Lambda handler Python file exists in lambda subdirectory."""
        assert lambda_handler_exists(terraform_dir)

    def test_config_tf_for_aws_config_rules(self, terraform_dir: Path):
        """Drift recoveries has config.tf for AWS Config rule integration."""
        assert (terraform_dir / "config.tf").is_file()

    @pytest.mark.parametrize("filename", DRIFT_RECOVERIES_EXTRA_FILES)
    def test_drift_specific_files_exist(self, terraform_dir: Path, filename: str):
        """Drift-specific Terraform files exist (parametrized)."""
        assert (terraform_dir / filename).exists(), f"{filename} missing"
