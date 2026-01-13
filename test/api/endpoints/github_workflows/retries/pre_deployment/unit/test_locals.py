"""Unit tests for locals.tf configuration."""


class TestLocalsConfiguration:
    """Tests for locals.tf Terraform configuration."""

    def test_locals_file_exists(self, retries_src_path):
        """Locals.tf file exists."""
        assert (retries_src_path / "locals.tf").exists()

    def test_locals_has_function_name(self, retries_src_path):
        """Locals defines function_name."""
        with open(retries_src_path / "locals.tf", encoding="utf-8") as f:
            content = f.read()
        assert "function_name" in content

    def test_locals_has_lambda_role_name(self, retries_src_path):
        """Locals defines lambda_role_name."""
        with open(retries_src_path / "locals.tf", encoding="utf-8") as f:
            content = f.read()
        assert "lambda_role_name" in content

    def test_locals_has_queue_name(self, retries_src_path):
        """Locals defines queue_name."""
        with open(retries_src_path / "locals.tf", encoding="utf-8") as f:
            content = f.read()
        assert "queue_name" in content

    def test_locals_has_dlq_name(self, retries_src_path):
        """Locals defines dlq_name."""
        with open(retries_src_path / "locals.tf", encoding="utf-8") as f:
            content = f.read()
        assert "dlq_name" in content

    def test_locals_has_common_tags(self, retries_src_path):
        """Locals defines common_tags."""
        with open(retries_src_path / "locals.tf", encoding="utf-8") as f:
            content = f.read()
        assert "common_tags" in content

    def test_locals_uses_resource_prefix(self, retries_src_path):
        """Locals uses resource_prefix from module.common."""
        with open(retries_src_path / "locals.tf", encoding="utf-8") as f:
            content = f.read()
        assert "module.common.resource_prefix" in content

    def test_locals_has_aws_region(self, retries_src_path):
        """Locals defines aws_region."""
        with open(retries_src_path / "locals.tf", encoding="utf-8") as f:
            content = f.read()
        assert "aws_region" in content

    def test_locals_has_aws_account_id(self, retries_src_path):
        """Locals defines aws_account_id."""
        with open(retries_src_path / "locals.tf", encoding="utf-8") as f:
            content = f.read()
        assert "aws_account_id" in content
