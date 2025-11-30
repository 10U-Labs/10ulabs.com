from test.health.conftest import HEALTH_SRC

BACKEND_FILE = HEALTH_SRC / "backend.tf"


def test_backend_terraform_file_exists():
    assert BACKEND_FILE.exists()


def test_backend_uses_s3():
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'backend "s3"' in content


def test_backend_uses_correct_bucket():
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'bucket       = "10ulabs-terraform-state"' in content


def test_backend_uses_correct_key():
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'key          = "health/terraform.tfstate"' in content


def test_backend_uses_encryption():
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'encrypt      = true' in content


def test_backend_uses_lockfile():
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'use_lockfile = true' in content


def test_backend_requires_terraform_version():
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'required_version = ">= 1.14"' in content


def test_backend_requires_archive_provider():
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'hashicorp/archive' in content


def test_backend_requires_aws_provider():
    with open(BACKEND_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'hashicorp/aws' in content
