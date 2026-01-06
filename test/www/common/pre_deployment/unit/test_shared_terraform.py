"""Unit tests for www/common shared.tf configuration."""


def test_shared_file_exists(src_dir):
    """Verify shared.tf file exists."""
    assert (src_dir / "shared.tf").exists()


def test_shared_common_module_defined(src_dir):
    """Verify common module is defined."""
    content = (src_dir / "shared.tf").read_text()
    assert 'module "common"' in content


def test_shared_module_source_path(src_dir):
    """Verify common module source path."""
    content = (src_dir / "shared.tf").read_text()
    assert 'source = "../../../lib/terraform/common"' in content
