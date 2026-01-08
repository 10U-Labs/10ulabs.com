"""Pre-deployment unit tests for api/common/networking shared.tf."""


def test_shared_file_exists(api_common_networking_dir):
    """Test that shared.tf file exists."""
    shared_tf = api_common_networking_dir / "shared.tf"
    assert shared_tf.exists()


def test_shared_defines_common_module(api_common_networking_dir):
    """Test that shared.tf defines the common module."""
    shared_tf = api_common_networking_dir / "shared.tf"
    content = shared_tf.read_text()
    assert 'module "common"' in content


def test_shared_module_has_source(api_common_networking_dir):
    """Test that common module has source attribute."""
    shared_tf = api_common_networking_dir / "shared.tf"
    content = shared_tf.read_text()
    assert "source" in content


def test_shared_module_source_is_lib_terraform_common(api_common_networking_dir):
    """Test that common module source points to lib/terraform/common."""
    shared_tf = api_common_networking_dir / "shared.tf"
    content = shared_tf.read_text()
    assert "lib/terraform/common" in content


def test_shared_module_source_uses_relative_path(api_common_networking_dir):
    """Test that common module source uses relative path."""
    shared_tf = api_common_networking_dir / "shared.tf"
    content = shared_tf.read_text()
    assert "../../../../lib/terraform/common" in content
