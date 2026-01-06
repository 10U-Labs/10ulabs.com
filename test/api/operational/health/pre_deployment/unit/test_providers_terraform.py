"""Unit tests for health endpoint providers.tf configuration."""


def test_providers_file_exists(health_src_dir):
    """Verify providers.tf file exists."""
    assert (health_src_dir / "providers.tf").exists()


def test_providers_aws_provider_defined(health_src_dir):
    """Verify AWS provider is defined."""
    content = (health_src_dir / "providers.tf").read_text()
    assert 'provider "aws"' in content


def test_providers_region_uses_local(health_src_dir):
    """Verify AWS provider region uses local.aws_region."""
    content = (health_src_dir / "providers.tf").read_text()
    assert "region = local.aws_region" in content


def test_providers_has_default_tags(health_src_dir):
    """Verify AWS provider has default_tags block."""
    content = (health_src_dir / "providers.tf").read_text()
    assert "default_tags {" in content


def test_providers_default_tags_managed_by_terraform(health_src_dir):
    """Verify default tags include ManagedBy = Terraform."""
    content = (health_src_dir / "providers.tf").read_text()
    assert 'ManagedBy  = "Terraform"' in content


def test_providers_default_tags_project_10uf(health_src_dir):
    """Verify default tags include Project = 10UF."""
    content = (health_src_dir / "providers.tf").read_text()
    assert 'Project    = "10UF"' in content


def test_providers_default_tags_repository(health_src_dir):
    """Verify default tags include Repository using local reference."""
    content = (health_src_dir / "providers.tf").read_text()
    assert "Repository = local.github_repo_full" in content


def test_providers_default_tags_stack_health(health_src_dir):
    """Verify default tags include Stack = health."""
    content = (health_src_dir / "providers.tf").read_text()
    assert 'Stack      = "health"' in content
