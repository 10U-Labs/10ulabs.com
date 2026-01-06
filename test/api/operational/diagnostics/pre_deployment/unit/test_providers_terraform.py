"""Unit tests for diagnostics endpoint providers.tf configuration."""


def test_providers_file_exists(diagnostics_src_dir):
    """Verify providers.tf file exists."""
    assert (diagnostics_src_dir / "providers.tf").exists()


def test_providers_aws_provider_defined(diagnostics_src_dir):
    """Verify AWS provider is defined."""
    content = (diagnostics_src_dir / "providers.tf").read_text()
    assert 'provider "aws"' in content


def test_providers_aws_region_from_local(diagnostics_src_dir):
    """Verify AWS provider uses local.aws_region for region."""
    content = (diagnostics_src_dir / "providers.tf").read_text()
    assert "region = local.aws_region" in content


def test_providers_has_default_tags_block(diagnostics_src_dir):
    """Verify AWS provider has default_tags block."""
    content = (diagnostics_src_dir / "providers.tf").read_text()
    assert "default_tags {" in content


def test_providers_default_tags_has_managed_by(diagnostics_src_dir):
    """Verify default_tags has ManagedBy tag."""
    content = (diagnostics_src_dir / "providers.tf").read_text()
    assert 'ManagedBy  = "Terraform"' in content


def test_providers_default_tags_has_project(diagnostics_src_dir):
    """Verify default_tags has Project tag."""
    content = (diagnostics_src_dir / "providers.tf").read_text()
    assert 'Project    = "10UF"' in content


def test_providers_default_tags_has_repository(diagnostics_src_dir):
    """Verify default_tags has Repository tag from local."""
    content = (diagnostics_src_dir / "providers.tf").read_text()
    assert "Repository = local.github_repo_full" in content


def test_providers_default_tags_has_stack(diagnostics_src_dir):
    """Verify default_tags has Stack tag."""
    content = (diagnostics_src_dir / "providers.tf").read_text()
    assert 'Stack      = "echo"' in content
