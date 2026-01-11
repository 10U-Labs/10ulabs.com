"""Shared test classes for Terraform file existence tests."""
from pathlib import Path
from typing import List, Optional

from test_utils import get_missing_terraform_files, lambda_handler_exists


class TerraformFilesExistTestMixin:
    """Test mixin that verifies Terraform files exist.

    Subclasses can define REQUIRED_TF_FILES to override the default list.
    If not defined or empty, uses DEFAULT_TERRAFORM_FILES from terraform_assertions.
    """

    REQUIRED_TF_FILES: Optional[List[str]] = None

    def test_all_required_terraform_files_exist(self, terraform_dir: Path):
        """All required Terraform files are present."""
        assert get_missing_terraform_files(terraform_dir, self.REQUIRED_TF_FILES) == []

    def test_lambda_handler_exists(self, terraform_dir: Path):
        """Lambda handler Python file exists."""
        assert lambda_handler_exists(terraform_dir)
