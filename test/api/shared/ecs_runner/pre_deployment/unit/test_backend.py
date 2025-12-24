"""Pre-deployment unit tests for api/shared/ecs_runner backend.tf configuration."""


def test_backend_uses_s3_backend(api_shared_ecs_runner_dir):
    """Test that backend.tf uses S3 backend."""
    content = (api_shared_ecs_runner_dir / "backend.tf").read_text()
    assert 'backend "s3"' in content


def test_backend_bucket_name(api_shared_ecs_runner_dir):
    """Test that backend uses the correct S3 bucket."""
    content = (api_shared_ecs_runner_dir / "backend.tf").read_text()
    assert 'bucket       = "10ulabs-terraform-state-us-east-2"' in content


def test_backend_key_path(api_shared_ecs_runner_dir):
    """Test that backend uses the correct state file key path."""
    content = (api_shared_ecs_runner_dir / "backend.tf").read_text()
    assert 'key          = "api/shared/ecs_runner/terraform.tfstate"' in content


def test_backend_region(api_shared_ecs_runner_dir):
    """Test that backend uses the correct AWS region."""
    content = (api_shared_ecs_runner_dir / "backend.tf").read_text()
    assert 'region       = "us-east-2"' in content


def test_backend_encryption_enabled(api_shared_ecs_runner_dir):
    """Test that backend has encryption enabled."""
    content = (api_shared_ecs_runner_dir / "backend.tf").read_text()
    assert "encrypt      = true" in content


def test_backend_uses_lockfile(api_shared_ecs_runner_dir):
    """Test that backend uses lockfile for state locking."""
    content = (api_shared_ecs_runner_dir / "backend.tf").read_text()
    assert "use_lockfile = true" in content
