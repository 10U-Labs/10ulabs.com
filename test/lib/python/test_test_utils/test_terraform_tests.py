"""Comprehensive tests for test_utils.terraform_tests module."""
import pytest

from test_utils.terraform_tests import TerraformFilesExistTestMixin


class TestTerraformFilesExistTestMixin:
    """Tests for TerraformFilesExistTestMixin class."""

    def test_required_files_check_fails_when_a_file_is_missing(self, tmp_path):
        """test_all_required_terraform_files_exist fails on an empty directory."""
        mixin = TerraformFilesExistTestMixin()
        with pytest.raises(AssertionError):
            mixin.test_all_required_terraform_files_exist(tmp_path)

    def test_handler_check_fails_when_handler_is_missing(self, tmp_path):
        """test_lambda_handler_exists fails when lambda/handler.py is absent."""
        mixin = TerraformFilesExistTestMixin()
        with pytest.raises(AssertionError):
            mixin.test_lambda_handler_exists(tmp_path)
