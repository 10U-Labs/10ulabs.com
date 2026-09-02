from pathlib import Path
def test_locals_file_exists(diagnostics_src_dir: Path) -> None:
    assert (diagnostics_src_dir / "locals.tf").exists()


def test_locals_has_locals_block(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "locals {" in content


def test_locals_has_aws_account_id(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "aws_account_id   = module.common.aws_account_id" in content


def test_locals_has_aws_region(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "aws_region       = module.common.aws_region" in content


def test_locals_has_github_repo_full(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "github_repo_full" in content


def test_locals_github_repo_full_uses_github_org(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "module.common.github_org" in content


def test_locals_github_repo_full_uses_name_for_github_repo(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "module.common.name_for_github_repo" in content


def test_locals_has_diagnostics_handler_role_name(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "diagnostics_handler_role_name" in content


def test_locals_diagnostics_handler_role_name_value(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "DiagnosticsHandlerServiceRole" in content


def test_locals_role_name_uses_resource_prefix(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "module.common.resource_prefix" in content


def test_locals_has_common_tags(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert "common_tags = {" in content


def test_locals_common_tags_has_managed_by(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert 'ManagedBy = "terraform"' in content


def test_locals_common_tags_has_purpose(diagnostics_src_dir: Path) -> None:
    content = (diagnostics_src_dir / "locals.tf").read_text()
    assert 'Purpose   = "diagnostics-endpoint"' in content
