"""Unit tests for www/common providers.tf configuration."""


def test_providers_file_exists(src_dir):
    """Verify providers.tf file exists."""
    assert (src_dir / "providers.tf").exists()


def test_providers_aws_provider_defined(src_dir):
    """Verify AWS provider is defined."""
    content = (src_dir / "providers.tf").read_text()
    assert 'provider "aws"' in content


def test_providers_region_uses_local(src_dir):
    """Verify AWS provider region uses local.aws_region."""
    content = (src_dir / "providers.tf").read_text()
    assert "region = local.aws_region" in content


def test_providers_has_default_tags(src_dir):
    """Verify AWS provider has default_tags block."""
    content = (src_dir / "providers.tf").read_text()
    assert "default_tags {" in content


def test_providers_default_tags_managed_by_terraform(src_dir):
    """Verify default tags include ManagedBy = Terraform."""
    content = (src_dir / "providers.tf").read_text()
    assert 'ManagedBy  = "Terraform"' in content


def test_providers_default_tags_project_10uf(src_dir):
    """Verify default tags include Project = 10UF."""
    content = (src_dir / "providers.tf").read_text()
    assert 'Project    = "10UF"' in content


def test_providers_default_tags_repository(src_dir):
    """Verify default tags include Repository using local reference."""
    content = (src_dir / "providers.tf").read_text()
    assert "Repository = local.github_repo_full" in content


def test_providers_default_tags_stack_website(src_dir):
    """Verify default tags include Stack = website."""
    content = (src_dir / "providers.tf").read_text()
    assert 'Stack      = "website"' in content


def test_providers_us_east_1_alias_defined(src_dir):
    """Verify us-east-1 provider alias is defined."""
    content = (src_dir / "providers.tf").read_text()
    assert 'alias  = "us-east-1"' in content


def test_providers_us_east_1_region_hardcoded(src_dir):
    """Verify us-east-1 provider region is hardcoded."""
    content = (src_dir / "providers.tf").read_text()
    assert 'region = "us-east-1"' in content
