from pathlib import Path
def test_backend_file_exists(src_dir: Path) -> None:
    assert (src_dir / "backend.tf").exists()


def test_backend_uses_s3_backend(src_dir: Path) -> None:
    content = (src_dir / "backend.tf").read_text()
    assert 'backend "s3"' in content


def test_backend_bucket_name(src_dir: Path) -> None:
    content = (src_dir / "backend.tf").read_text()
    assert 'bucket       = "10ulabs-terraform-state-us-east-2"' in content


def test_backend_key_path(src_dir: Path) -> None:
    content = (src_dir / "backend.tf").read_text()
    assert 'key          = "website/terraform.tfstate"' in content


def test_backend_region(src_dir: Path) -> None:
    content = (src_dir / "backend.tf").read_text()
    assert 'region       = "us-east-2"' in content


def test_backend_encryption_enabled(src_dir: Path) -> None:
    content = (src_dir / "backend.tf").read_text()
    assert "encrypt      = true" in content


def test_backend_uses_lockfile(src_dir: Path) -> None:
    content = (src_dir / "backend.tf").read_text()
    assert "use_lockfile = true" in content


def test_backend_terraform_block_exists(src_dir: Path) -> None:
    content = (src_dir / "backend.tf").read_text()
    assert "terraform {" in content


def test_backend_required_version(src_dir: Path) -> None:
    content = (src_dir / "backend.tf").read_text()
    assert 'required_version = ">= 1.14"' in content


def test_backend_required_providers_aws(src_dir: Path) -> None:
    content = (src_dir / "backend.tf").read_text()
    assert "aws = {" in content


def test_backend_aws_provider_source(src_dir: Path) -> None:
    content = (src_dir / "backend.tf").read_text()
    assert 'source  = "hashicorp/aws"' in content


def test_backend_aws_provider_version(src_dir: Path) -> None:
    content = (src_dir / "backend.tf").read_text()
    assert 'version = "~> 5.0"' in content


def test_backend_archive_provider_required(src_dir: Path) -> None:
    content = (src_dir / "backend.tf").read_text()
    assert "archive = {" in content


def test_backend_archive_provider_source(src_dir: Path) -> None:
    content = (src_dir / "backend.tf").read_text()
    assert 'source  = "hashicorp/archive"' in content
