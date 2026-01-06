"""Unit tests for diagnostics endpoint locals.tf configuration."""


def test_locals_file_exists(diagnostics_src_dir):
    """Verify locals.tf file exists."""
    assert (diagnostics_src_dir / "locals.tf").exists()


def test_locals_has_locals_block(diagnostics_src_dir):
    """Verify locals.tf has a locals block."""
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "locals {" in content


def test_locals_has_aws_account_id(diagnostics_src_dir):
    """Verify locals defines aws_account_id from common module."""
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "aws_account_id   = module.common.aws_account_id" in content


def test_locals_has_aws_region(diagnostics_src_dir):
    """Verify locals defines aws_region from common module."""
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "aws_region       = module.common.aws_region" in content


def test_locals_has_github_repo_full(diagnostics_src_dir):
    """Verify locals defines github_repo_full from common module."""
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "github_repo_full" in content
    assert "module.common.github_org" in content
    assert "module.common.name_for_github_repo" in content


def test_locals_has_diagnostics_handler_role_name(diagnostics_src_dir):
    """Verify locals defines diagnostics_handler_role_name."""
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "diagnostics_handler_role_name" in content
    assert "DiagnosticsHandlerServiceRole" in content


def test_locals_role_name_uses_resource_prefix(diagnostics_src_dir):
    """Verify role name uses module.common.resource_prefix."""
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "module.common.resource_prefix" in content


def test_locals_has_common_tags(diagnostics_src_dir):
    """Verify locals defines common_tags."""
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "common_tags = {" in content


def test_locals_common_tags_has_managed_by(diagnostics_src_dir):
    """Verify common_tags has ManagedBy set to terraform."""
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert 'ManagedBy = "terraform"' in content


def test_locals_common_tags_has_purpose(diagnostics_src_dir):
    """Verify common_tags has Purpose set to diagnostics-endpoint."""
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert 'Purpose   = "diagnostics-endpoint"' in content
