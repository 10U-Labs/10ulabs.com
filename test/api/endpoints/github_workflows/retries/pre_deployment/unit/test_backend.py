"""Unit tests for backend.tf configuration."""


class TestBackendConfiguration:
    """Tests for backend.tf Terraform configuration."""

    def test_backend_file_exists(self, retries_src_path):
        """Backend.tf file exists."""
        assert (retries_src_path / "backend.tf").exists()

    def test_backend_uses_s3(self, retries_src_path):
        """Backend configuration uses S3."""
        with open(retries_src_path / "backend.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'backend "s3"' in content

    def test_backend_has_bucket(self, retries_src_path):
        """Backend configuration specifies a bucket."""
        with open(retries_src_path / "backend.tf", encoding="utf-8") as f:
            content = f.read()
        assert "bucket" in content

    def test_backend_has_key(self, retries_src_path):
        """Backend configuration specifies a state key."""
        with open(retries_src_path / "backend.tf", encoding="utf-8") as f:
            content = f.read()
        assert "key" in content

    def test_backend_has_region(self, retries_src_path):
        """Backend configuration specifies a region."""
        with open(retries_src_path / "backend.tf", encoding="utf-8") as f:
            content = f.read()
        assert "region" in content
