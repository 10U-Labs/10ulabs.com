"""Tests for backend.tf Terraform configuration."""
from pathlib import Path


def _get_backend_tf_path() -> Path:
    """Get the path to backend.tf file."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent
    return base / "src" / "api" / "backend" / "backend.tf"


def test_backend_terraform_file_exists():
    """Verify backend.tf file exists."""
    assert _get_backend_tf_path().exists()


def test_backend_has_null_provider():
    """Verify backend.tf has null provider configured."""
    with open(_get_backend_tf_path(), encoding="utf-8") as f:
        content = f.read()
    assert "hashicorp/null" in content
