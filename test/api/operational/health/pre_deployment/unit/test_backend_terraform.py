"""Unit tests for health endpoint backend.tf configuration."""


def test_backend_uses_s3_backend(health_src_dir):
    """Verify backend.tf uses S3 backend."""
    content = (health_src_dir / "backend.tf").read_text()
    assert 'backend "s3"' in content


def test_backend_bucket_name(health_src_dir):
    """Verify backend uses the correct S3 bucket."""
    content = (health_src_dir / "backend.tf").read_text()
    assert 'bucket       = "10ulabs-terraform-state-us-east-2"' in content


def test_backend_key_path(health_src_dir):
    """Verify backend uses the correct state file key path."""
    content = (health_src_dir / "backend.tf").read_text()
    assert 'key          = "health/terraform.tfstate"' in content


def test_backend_region(health_src_dir):
    """Verify backend uses the correct AWS region."""
    content = (health_src_dir / "backend.tf").read_text()
    assert 'region       = "us-east-2"' in content


def test_backend_encryption_enabled(health_src_dir):
    """Verify backend has encryption enabled."""
    content = (health_src_dir / "backend.tf").read_text()
    assert "encrypt      = true" in content


def test_backend_uses_lockfile(health_src_dir):
    """Verify backend uses lockfile for state locking."""
    content = (health_src_dir / "backend.tf").read_text()
    assert "use_lockfile = true" in content
