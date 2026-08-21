"""Comprehensive tests for test_utils.terraform_assertions module."""
from test_utils.terraform_assertions import (
    DEFAULT_TERRAFORM_FILES,
    get_missing_terraform_files,
    lambda_handler_exists,
)


class TestGetMissingTerraformFiles:
    """Tests for get_missing_terraform_files function."""

    def test_returns_missing_names_in_required_order(self, tmp_path):
        """get_missing_terraform_files keeps the order the files were required."""
        (tmp_path / "locals.tf").touch()
        required = ["backend.tf", "locals.tf", "iam.tf"]
        result = get_missing_terraform_files(tmp_path, required)
        assert result == ["backend.tf", "iam.tf"]

    def test_returns_empty_list_when_all_present(self, tmp_path):
        """get_missing_terraform_files returns [] when nothing is absent."""
        (tmp_path / "outputs.tf").touch()
        result = get_missing_terraform_files(tmp_path, ["outputs.tf"])
        assert result == []

    def test_uses_default_files_when_required_is_none(self, tmp_path):
        """get_missing_terraform_files falls back to DEFAULT_TERRAFORM_FILES."""
        assert get_missing_terraform_files(tmp_path) == DEFAULT_TERRAFORM_FILES

    def test_returns_empty_list_for_empty_required_list(self, tmp_path):
        """get_missing_terraform_files requires nothing of an empty list."""
        assert get_missing_terraform_files(tmp_path, []) == []


class TestLambdaHandlerExists:
    """Tests for lambda_handler_exists function."""

    def test_returns_true_when_handler_present(self, tmp_path):
        """lambda_handler_exists finds lambda/handler.py under the directory."""
        handler_dir = tmp_path / "lambda"
        handler_dir.mkdir()
        (handler_dir / "handler.py").touch()
        assert lambda_handler_exists(tmp_path) is True

    def test_returns_false_when_handler_absent(self, tmp_path):
        """lambda_handler_exists reports a directory with no handler."""
        assert lambda_handler_exists(tmp_path) is False
