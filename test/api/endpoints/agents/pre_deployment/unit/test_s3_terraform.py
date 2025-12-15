"""Unit tests for agents S3 Terraform configuration."""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


def test_s3_terraform_file_exists():
    """Verify s3.tf file exists."""
    s3_file = AGENTS_SRC / "s3.tf"
    assert s3_file.exists()


def test_s3_prompts_bucket_resource_exists():
    """Verify S3 bucket for prompts is defined."""
    s3_file = AGENTS_SRC / "s3.tf"
    with open(s3_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_bucket" "prompts"' in content


def test_s3_bucket_versioning_resource_exists():
    """Verify S3 bucket versioning resource is defined."""
    s3_file = AGENTS_SRC / "s3.tf"
    with open(s3_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_bucket_versioning"' in content


def test_s3_bucket_versioning_enabled():
    """Verify S3 bucket versioning status is Enabled."""
    s3_file = AGENTS_SRC / "s3.tf"
    with open(s3_file, encoding="utf-8") as f:
        content = f.read()
    assert 'status = "Enabled"' in content


def test_s3_bucket_encryption_resource_exists():
    """Verify S3 bucket encryption resource is defined."""
    s3_file = AGENTS_SRC / "s3.tf"
    with open(s3_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_bucket_server_side_encryption_configuration"' in content


def test_s3_bucket_uses_aes256():
    """Verify S3 bucket uses AES256 encryption."""
    s3_file = AGENTS_SRC / "s3.tf"
    with open(s3_file, encoding="utf-8") as f:
        content = f.read()
    assert "AES256" in content


def test_s3_bucket_public_access_block_exists():
    """Verify S3 bucket public access block resource is defined."""
    s3_file = AGENTS_SRC / "s3.tf"
    with open(s3_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_bucket_public_access_block"' in content


def test_s3_bucket_blocks_public_acls():
    """Verify S3 bucket blocks public ACLs."""
    s3_file = AGENTS_SRC / "s3.tf"
    with open(s3_file, encoding="utf-8") as f:
        content = f.read()
    assert "block_public_acls" in content


def test_s3_bucket_blocks_public_policy():
    """Verify S3 bucket blocks public policy."""
    s3_file = AGENTS_SRC / "s3.tf"
    with open(s3_file, encoding="utf-8") as f:
        content = f.read()
    assert "block_public_policy" in content


def test_s3_object_resource_exists():
    """Verify S3 object resource for prompts is defined."""
    s3_file = AGENTS_SRC / "s3.tf"
    with open(s3_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_object" "prompts"' in content


def test_s3_bucket_uploads_prompts():
    """Verify S3 bucket uploads prompts from prompts directory."""
    s3_file = AGENTS_SRC / "s3.tf"
    with open(s3_file, encoding="utf-8") as f:
        content = f.read()
    assert "prompts/" in content
