from pathlib import Path


def test_backend_terraform_file_exists():
    backend_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "backend.tf"
    assert backend_file.exists()


def test_backend_has_null_provider():
    backend_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "backend.tf"
    with open(backend_file, encoding="utf-8") as f:
        content = f.read()
    assert "hashicorp/null" in content
