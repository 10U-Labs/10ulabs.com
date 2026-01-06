"""Unit tests for www/common backend.tf configuration."""


def test_backend_file_exists(src_dir):
    """Verify backend.tf file exists."""
    assert (src_dir / "backend.tf").exists()


def test_backend_uses_s3_backend(src_dir):
    """Verify backend.tf uses S3 backend."""
    content = (src_dir / "backend.tf").read_text()
    assert 'backend "s3"' in content


def test_backend_bucket_name(src_dir):
    """Verify backend uses the correct S3 bucket."""
    content = (src_dir / "backend.tf").read_text()
    assert 'bucket       = "10ulabs-terraform-state-us-east-2"' in content


def test_backend_key_path(src_dir):
    """Verify backend uses the correct state file key path."""
    content = (src_dir / "backend.tf").read_text()
    assert 'key          = "website/terraform.tfstate"' in content


def test_backend_region(src_dir):
    """Verify backend uses the correct AWS region."""
    content = (src_dir / "backend.tf").read_text()
    assert 'region       = "us-east-2"' in content


def test_backend_encryption_enabled(src_dir):
    """Verify backend has encryption enabled."""
    content = (src_dir / "backend.tf").read_text()
    assert "encrypt      = true" in content


def test_backend_uses_lockfile(src_dir):
    """Verify backend uses lockfile for state locking."""
    content = (src_dir / "backend.tf").read_text()
    assert "use_lockfile = true" in content


def test_backend_terraform_block_exists(src_dir):
    """Verify terraform block exists."""
    content = (src_dir / "backend.tf").read_text()
    assert "terraform {" in content


def test_backend_required_version(src_dir):
    """Verify required Terraform version is specified."""
    content = (src_dir / "backend.tf").read_text()
    assert 'required_version = ">= 1.14"' in content


def test_backend_required_providers_aws(src_dir):
    """Verify AWS provider is in required_providers."""
    content = (src_dir / "backend.tf").read_text()
    assert "aws = {" in content


def test_backend_aws_provider_source(src_dir):
    """Verify AWS provider source is hashicorp/aws."""
    content = (src_dir / "backend.tf").read_text()
    assert 'source  = "hashicorp/aws"' in content


def test_backend_aws_provider_version(src_dir):
    """Verify AWS provider version constraint."""
    content = (src_dir / "backend.tf").read_text()
    assert 'version = "~> 5.0"' in content


def test_backend_archive_provider_required(src_dir):
    """Verify archive provider is in required_providers."""
    content = (src_dir / "backend.tf").read_text()
    assert "archive = {" in content


def test_backend_archive_provider_source(src_dir):
    """Verify archive provider source is hashicorp/archive."""
    content = (src_dir / "backend.tf").read_text()
    assert 'source  = "hashicorp/archive"' in content
