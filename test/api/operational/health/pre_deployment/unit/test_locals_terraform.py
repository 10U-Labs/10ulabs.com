from pathlib import Path
def test_locals_file_exists(health_src_dir: Path) -> None:
    assert (health_src_dir / "locals.tf").exists()


def test_locals_block_exists(health_src_dir: Path) -> None:
    content = (health_src_dir / "locals.tf").read_text()
    assert "locals {" in content


def test_locals_aws_account_id_references_module_common(health_src_dir: Path) -> None:
    content = (health_src_dir / "locals.tf").read_text()
    assert "aws_account_id   = module.common.aws_account_id" in content


def test_locals_aws_region_references_module_common(health_src_dir: Path) -> None:
    content = (health_src_dir / "locals.tf").read_text()
    assert "aws_region       = module.common.aws_region" in content


def test_locals_resource_prefix_references_module_common(health_src_dir: Path) -> None:
    content = (health_src_dir / "locals.tf").read_text()
    assert "resource_prefix  = module.common.resource_prefix" in content


def test_locals_github_repo_full_defined(health_src_dir: Path) -> None:
    content = (health_src_dir / "locals.tf").read_text()
    assert "github_repo_full" in content


def test_locals_github_repo_full_uses_github_org(health_src_dir: Path) -> None:
    content = (health_src_dir / "locals.tf").read_text()
    assert "module.common.github_org" in content


def test_locals_github_repo_full_uses_name_for_github_repo(health_src_dir: Path) -> None:
    content = (health_src_dir / "locals.tf").read_text()
    assert "module.common.name_for_github_repo" in content


def test_locals_lambda_role_name_defined(health_src_dir: Path) -> None:
    content = (health_src_dir / "locals.tf").read_text()
    assert "lambda_role_name" in content


def test_locals_lambda_role_name_value(health_src_dir: Path) -> None:
    content = (health_src_dir / "locals.tf").read_text()
    assert "HealthHandlerServiceRole" in content


def test_locals_common_tags_defined(health_src_dir: Path) -> None:
    content = (health_src_dir / "locals.tf").read_text()
    assert "common_tags = {" in content


def test_locals_common_tags_managed_by_terraform(health_src_dir: Path) -> None:
    content = (health_src_dir / "locals.tf").read_text()
    assert 'ManagedBy = "terraform"' in content


def test_locals_common_tags_purpose_health_check(health_src_dir: Path) -> None:
    content = (health_src_dir / "locals.tf").read_text()
    assert 'Purpose   = "health-check"' in content
