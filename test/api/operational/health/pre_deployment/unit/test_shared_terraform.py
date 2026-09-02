from pathlib import Path
def test_shared_file_exists(health_src_dir: Path) -> None:
    assert (health_src_dir / "shared.tf").exists()


def test_shared_common_module_defined(health_src_dir: Path) -> None:
    content = (health_src_dir / "shared.tf").read_text()
    assert 'module "common"' in content


def test_shared_common_module_source_path(health_src_dir: Path) -> None:
    content = (health_src_dir / "shared.tf").read_text()
    assert 'source = "../../../../lib/terraform/common"' in content


def test_shared_api_remote_state_defined(health_src_dir: Path) -> None:
    content = (health_src_dir / "shared.tf").read_text()
    assert 'data "terraform_remote_state" "api"' in content


def test_shared_api_remote_state_backend_s3(health_src_dir: Path) -> None:
    content = (health_src_dir / "shared.tf").read_text()
    assert 'backend = "s3"' in content


def test_shared_api_remote_state_bucket(health_src_dir: Path) -> None:
    content = (health_src_dir / "shared.tf").read_text()
    assert 'bucket = "10ulabs-terraform-state-us-east-2"' in content


def test_shared_api_remote_state_key(health_src_dir: Path) -> None:
    content = (health_src_dir / "shared.tf").read_text()
    assert 'key    = "api/terraform.tfstate"' in content


def test_shared_api_remote_state_region(health_src_dir: Path) -> None:
    content = (health_src_dir / "shared.tf").read_text()
    assert 'region = "us-east-2"' in content
