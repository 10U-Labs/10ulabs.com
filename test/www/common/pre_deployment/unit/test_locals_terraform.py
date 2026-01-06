"""Unit tests for www/common locals.tf configuration."""


def test_locals_file_exists(src_dir):
    """Verify locals.tf file exists."""
    assert (src_dir / "locals.tf").exists()


def test_locals_block_exists(src_dir):
    """Verify locals block is defined."""
    content = (src_dir / "locals.tf").read_text()
    assert "locals {" in content


def test_locals_aws_region_references_module_common(src_dir):
    """Verify aws_region uses module.common."""
    content = (src_dir / "locals.tf").read_text()
    assert "aws_region            = module.common.aws_region" in content


def test_locals_domain_name_references_module_common(src_dir):
    """Verify domain_name uses module.common."""
    content = (src_dir / "locals.tf").read_text()
    assert "domain_name           = module.common.domain_name" in content


def test_locals_apex_fqdn_equals_domain_name(src_dir):
    """Verify apex_fqdn equals domain_name."""
    content = (src_dir / "locals.tf").read_text()
    assert "apex_fqdn             = module.common.domain_name" in content


def test_locals_www_fqdn_has_www_prefix(src_dir):
    """Verify www_fqdn has www. prefix."""
    content = (src_dir / "locals.tf").read_text()
    assert 'www_fqdn              = "www.${module.common.domain_name}"' in content


def test_locals_website_bucket_name_defined(src_dir):
    """Verify website_bucket_name is defined."""
    content = (src_dir / "locals.tf").read_text()
    assert "website_bucket_name" in content


def test_locals_github_repo_full_defined(src_dir):
    """Verify github_repo_full is defined."""
    content = (src_dir / "locals.tf").read_text()
    assert "github_repo_full" in content


def test_locals_github_repo_full_uses_github_org(src_dir):
    """Verify github_repo_full uses github_org."""
    content = (src_dir / "locals.tf").read_text()
    assert "module.common.github_org" in content


def test_locals_github_repo_full_uses_name_for_github_repo(src_dir):
    """Verify github_repo_full uses name_for_github_repo."""
    content = (src_dir / "locals.tf").read_text()
    assert "module.common.name_for_github_repo" in content


def test_locals_name_for_central_logs_defined(src_dir):
    """Verify name_for_central_logs is defined."""
    content = (src_dir / "locals.tf").read_text()
    assert "name_for_central_logs" in content


def test_locals_name_for_central_logs_uses_module_common(src_dir):
    """Verify name_for_central_logs uses module.common."""
    content = (src_dir / "locals.tf").read_text()
    assert "module.common.name_for_central_logs_bucket" in content


def test_locals_resource_prefix_defined(src_dir):
    """Verify resource_prefix is defined."""
    content = (src_dir / "locals.tf").read_text()
    assert "resource_prefix" in content


def test_locals_resource_prefix_includes_website(src_dir):
    """Verify resource_prefix includes Website suffix."""
    content = (src_dir / "locals.tf").read_text()
    assert '"${module.common.resource_prefix}Website"' in content


def test_locals_common_tags_defined(src_dir):
    """Verify common_tags is defined."""
    content = (src_dir / "locals.tf").read_text()
    assert "common_tags = {" in content


def test_locals_common_tags_managed_by_terraform(src_dir):
    """Verify common_tags includes ManagedBy = terraform."""
    content = (src_dir / "locals.tf").read_text()
    assert 'ManagedBy = "terraform"' in content


def test_locals_common_tags_purpose(src_dir):
    """Verify common_tags includes Purpose."""
    content = (src_dir / "locals.tf").read_text()
    assert 'Purpose   = "website-infrastructure"' in content
