def test_providers_file_exists(health_src_dir):
    assert (health_src_dir / "providers.tf").exists()


def test_providers_aws_provider_defined(health_src_dir):
    content = (health_src_dir / "providers.tf").read_text()
    assert 'provider "aws"' in content


def test_providers_region_uses_local(health_src_dir):
    content = (health_src_dir / "providers.tf").read_text()
    assert "region = local.aws_region" in content


def test_providers_has_default_tags(health_src_dir):
    content = (health_src_dir / "providers.tf").read_text()
    assert "default_tags {" in content


def test_providers_default_tags_managed_by_terraform(health_src_dir):
    content = (health_src_dir / "providers.tf").read_text()
    assert 'ManagedBy  = "Terraform"' in content


def test_providers_default_tags_project_10uf(health_src_dir):
    content = (health_src_dir / "providers.tf").read_text()
    assert 'Project    = "10UF"' in content


def test_providers_default_tags_repository(health_src_dir):
    content = (health_src_dir / "providers.tf").read_text()
    assert "Repository = local.github_repo_full" in content


def test_providers_default_tags_stack_health(health_src_dir):
    content = (health_src_dir / "providers.tf").read_text()
    assert 'Stack      = "health"' in content
