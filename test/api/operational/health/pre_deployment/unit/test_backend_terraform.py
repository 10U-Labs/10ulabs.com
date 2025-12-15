"""Unit tests for health endpoint backend Terraform configuration."""
from test.api.operational.health.conftest import HEALTH_SRC

BACKEND_FILE = HEALTH_SRC / "backend.tf"


def test_backend_terraform_file_exists():
    """Verify backend.tf file exists."""
    assert BACKEND_FILE.exists()


def test_backend_uses_s3():
    """Verify S3 backend is configured."""
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'backend "s3"' in content


def test_backend_uses_correct_bucket():
    """Verify correct S3 bucket is used."""
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'bucket       = "10ulabs-terraform-state-us-east-2"' in content


def test_backend_uses_correct_key():
    """Verify correct state file key is used."""
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'key          = "health/terraform.tfstate"' in content


def test_backend_uses_encryption():
    """Verify state file encryption is enabled."""
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'encrypt      = true' in content


def test_backend_uses_lockfile():
    """Verify state locking is enabled."""
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'use_lockfile = true' in content


def test_backend_requires_terraform_version():
    """Verify Terraform version requirement."""
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'required_version = ">= 1.14"' in content


def test_backend_requires_archive_provider():
    """Verify archive provider requirement."""
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'hashicorp/archive' in content


def test_backend_requires_aws_provider():
    """Verify AWS provider requirement."""
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'hashicorp/aws' in content
