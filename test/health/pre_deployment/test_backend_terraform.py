from pathlib import Path


def test_backend_terraform_file_exists():
    backend_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "backend.tf"
    assert backend_file.exists()


def test_backend_uses_s3():
    backend_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "backend.tf"
    with open(backend_file, encoding="utf-8") as f:
        content = f.read()
    assert 'backend "s3"' in content


def test_backend_uses_correct_bucket():
    backend_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "backend.tf"
    with open(backend_file, encoding="utf-8") as f:
        content = f.read()
    assert 'bucket       = "10ulabs-terraform-state"' in content


def test_backend_uses_correct_key():
    backend_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "backend.tf"
    with open(backend_file, encoding="utf-8") as f:
        content = f.read()
    assert 'key          = "health/terraform.tfstate"' in content


def test_backend_uses_encryption():
    backend_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "backend.tf"
    with open(backend_file, encoding="utf-8") as f:
        content = f.read()
    assert 'encrypt      = true' in content


def test_backend_uses_lockfile():
    backend_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "backend.tf"
    with open(backend_file, encoding="utf-8") as f:
        content = f.read()
    assert 'use_lockfile = true' in content


def test_backend_requires_terraform_version():
    backend_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "backend.tf"
    with open(backend_file, encoding="utf-8") as f:
        content = f.read()
    assert 'required_version = ">= 1.14"' in content


def test_backend_requires_archive_provider():
    backend_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "backend.tf"
    with open(backend_file, encoding="utf-8") as f:
        content = f.read()
    assert 'hashicorp/archive' in content


def test_backend_requires_aws_provider():
    backend_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "backend.tf"
    with open(backend_file, encoding="utf-8") as f:
        content = f.read()
    assert 'hashicorp/aws' in content
