"""Unit tests for health endpoint shared.tf configuration."""


def test_shared_file_exists(health_src_dir):
    """Verify shared.tf file exists."""
    assert (health_src_dir / "shared.tf").exists()


def test_shared_common_module_defined(health_src_dir):
    """Verify common module is defined."""
    content = (health_src_dir / "shared.tf").read_text()
    assert 'module "common"' in content


def test_shared_common_module_source_path(health_src_dir):
    """Verify common module source points to lib/terraform/common."""
    content = (health_src_dir / "shared.tf").read_text()
    assert 'source = "../../../../lib/terraform/common"' in content


def test_shared_api_remote_state_defined(health_src_dir):
    """Verify terraform_remote_state for api is defined."""
    content = (health_src_dir / "shared.tf").read_text()
    assert 'data "terraform_remote_state" "api"' in content


def test_shared_api_remote_state_backend_s3(health_src_dir):
    """Verify api remote state uses S3 backend."""
    content = (health_src_dir / "shared.tf").read_text()
    assert 'backend = "s3"' in content


def test_shared_api_remote_state_bucket(health_src_dir):
    """Verify api remote state uses correct bucket."""
    content = (health_src_dir / "shared.tf").read_text()
    assert 'bucket = "10ulabs-terraform-state-us-east-2"' in content


def test_shared_api_remote_state_key(health_src_dir):
    """Verify api remote state uses correct key path."""
    content = (health_src_dir / "shared.tf").read_text()
    assert 'key    = "api/terraform.tfstate"' in content


def test_shared_api_remote_state_region(health_src_dir):
    """Verify api remote state uses correct region."""
    content = (health_src_dir / "shared.tf").read_text()
    assert 'region = "us-east-2"' in content
