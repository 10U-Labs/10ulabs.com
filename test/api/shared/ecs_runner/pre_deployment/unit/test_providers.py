"""Pre-deployment unit tests for api/shared/ecs_runner providers.tf configuration."""


def test_terraform_version_constraint(api_shared_ecs_runner_dir):
    """Test that Terraform version constraint is >= 1.10."""
    content = (api_shared_ecs_runner_dir / "providers.tf").read_text()
    assert 'required_version = ">= 1.10"' in content


def test_aws_provider_source(api_shared_ecs_runner_dir):
    """Test that AWS provider uses hashicorp/aws source."""
    content = (api_shared_ecs_runner_dir / "providers.tf").read_text()
    assert 'source  = "hashicorp/aws"' in content


def test_aws_provider_version_constraint(api_shared_ecs_runner_dir):
    """Test that AWS provider version constraint is ~> 6.18."""
    content = (api_shared_ecs_runner_dir / "providers.tf").read_text()
    assert 'version = "~> 6.18"' in content


def test_aws_provider_uses_local_region(api_shared_ecs_runner_dir):
    """Test that AWS provider uses local.aws_region for region."""
    content = (api_shared_ecs_runner_dir / "providers.tf").read_text()
    assert "region = local.aws_region" in content
