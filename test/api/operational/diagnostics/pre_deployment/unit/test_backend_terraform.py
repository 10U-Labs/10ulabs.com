from pathlib import Path
def test_backend_uses_s3_backend(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "backend.tf").read_text()
    assert 'backend "s3"' in content


def test_backend_bucket_name(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "backend.tf").read_text()
    assert 'bucket       = "10ulabs-terraform-state-us-east-2"' in content


def test_backend_key_path(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "backend.tf").read_text()
    assert 'key          = "diagnostics/terraform.tfstate"' in content


def test_backend_region(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "backend.tf").read_text()
    assert 'region       = "us-east-2"' in content


def test_backend_encryption_enabled(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "backend.tf").read_text()
    assert "encrypt      = true" in content


def test_backend_uses_lockfile(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "backend.tf").read_text()
    assert "use_lockfile = true" in content


def test_backend_required_version(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "backend.tf").read_text()
    assert 'required_version = ">= 1.14"' in content


def test_backend_requires_archive_provider(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "backend.tf").read_text()
    assert 'source  = "hashicorp/archive"' in content


def test_backend_requires_aws_provider(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "backend.tf").read_text()
    assert 'source  = "hashicorp/aws"' in content
