def test_providers_file_exists(src_dir):
    assert (src_dir / "providers.tf").exists()


def test_providers_aws_provider_defined(src_dir):
    content = (src_dir / "providers.tf").read_text()
    assert 'provider "aws"' in content


def test_providers_region_uses_local(src_dir):
    content = (src_dir / "providers.tf").read_text()
    assert "region = local.aws_region" in content


def test_providers_has_default_tags(src_dir):
    content = (src_dir / "providers.tf").read_text()
    assert "default_tags {" in content


def test_providers_default_tags_managed_by_terraform(src_dir):
    content = (src_dir / "providers.tf").read_text()
    assert 'ManagedBy  = "Terraform"' in content


def test_providers_default_tags_project_10uf(src_dir):
    content = (src_dir / "providers.tf").read_text()
    assert 'Project    = "10UF"' in content


def test_providers_default_tags_repository(src_dir):
    content = (src_dir / "providers.tf").read_text()
    assert "Repository = local.github_repo_full" in content


def test_providers_default_tags_stack_website(src_dir):
    content = (src_dir / "providers.tf").read_text()
    assert 'Stack      = "website"' in content


def test_providers_us_east_1_alias_defined(src_dir):
    content = (src_dir / "providers.tf").read_text()
    assert 'alias  = "us-east-1"' in content


def test_providers_us_east_1_region_hardcoded(src_dir):
    content = (src_dir / "providers.tf").read_text()
    assert 'region = "us-east-1"' in content
