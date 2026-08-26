def test_shared_file_exists(diagnostics_src_dir):
    assert (diagnostics_src_dir / "shared.tf").exists()


def test_shared_uses_common_module(diagnostics_src_dir):
    content = (diagnostics_src_dir / "shared.tf").read_text()
    assert 'module "common"' in content


def test_shared_common_module_source_path(diagnostics_src_dir):
    content = (diagnostics_src_dir / "shared.tf").read_text()
    assert 'source = "../../../../lib/terraform/common"' in content


def test_shared_has_terraform_remote_state(diagnostics_src_dir):
    content = (diagnostics_src_dir / "shared.tf").read_text()
    assert 'data "terraform_remote_state" "api"' in content


def test_shared_remote_state_uses_s3_backend(diagnostics_src_dir):
    content = (diagnostics_src_dir / "shared.tf").read_text()
    assert 'backend = "s3"' in content


def test_shared_remote_state_bucket_from_module(diagnostics_src_dir):
    content = (diagnostics_src_dir / "shared.tf").read_text()
    assert "bucket = module.common.name_for_terraform_state_bucket" in content


def test_shared_remote_state_key_path(diagnostics_src_dir):
    content = (diagnostics_src_dir / "shared.tf").read_text()
    assert 'key    = "api/terraform.tfstate"' in content


def test_shared_remote_state_region_from_module(diagnostics_src_dir):
    content = (diagnostics_src_dir / "shared.tf").read_text()
    assert "region = module.common.aws_region" in content
