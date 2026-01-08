"""Pre-deployment unit tests for api/common/networking backend.tf."""


def test_backend_file_exists(api_common_networking_dir):
    """Test that backend.tf file exists."""
    backend_tf = api_common_networking_dir / "backend.tf"
    assert backend_tf.exists()


def test_backend_uses_s3(api_common_networking_dir):
    """Test that backend uses S3."""
    backend_tf = api_common_networking_dir / "backend.tf"
    content = backend_tf.read_text()
    assert 'backend "s3"' in content


def test_backend_specifies_bucket(api_common_networking_dir):
    """Test that backend specifies bucket."""
    backend_tf = api_common_networking_dir / "backend.tf"
    content = backend_tf.read_text()
    assert "bucket" in content


def test_backend_bucket_is_terraform_state(api_common_networking_dir):
    """Test that backend uses correct state bucket."""
    backend_tf = api_common_networking_dir / "backend.tf"
    content = backend_tf.read_text()
    assert "10ulabs-terraform-state-us-east-2" in content


def test_backend_specifies_key(api_common_networking_dir):
    """Test that backend specifies key."""
    backend_tf = api_common_networking_dir / "backend.tf"
    content = backend_tf.read_text()
    assert "key" in content


def test_backend_key_is_networking_path(api_common_networking_dir):
    """Test that backend key is the networking state path."""
    backend_tf = api_common_networking_dir / "backend.tf"
    content = backend_tf.read_text()
    assert "api/common/networking/terraform.tfstate" in content


def test_backend_specifies_region(api_common_networking_dir):
    """Test that backend specifies region."""
    backend_tf = api_common_networking_dir / "backend.tf"
    content = backend_tf.read_text()
    assert "region" in content


def test_backend_region_is_us_east_2(api_common_networking_dir):
    """Test that backend region is us-east-2."""
    backend_tf = api_common_networking_dir / "backend.tf"
    content = backend_tf.read_text()
    assert 'region       = "us-east-2"' in content


def test_backend_has_encryption_enabled(api_common_networking_dir):
    """Test that backend has encryption enabled."""
    backend_tf = api_common_networking_dir / "backend.tf"
    content = backend_tf.read_text()
    assert "encrypt      = true" in content


def test_backend_has_lockfile_enabled(api_common_networking_dir):
    """Test that backend uses lockfile."""
    backend_tf = api_common_networking_dir / "backend.tf"
    content = backend_tf.read_text()
    assert "use_lockfile = true" in content
