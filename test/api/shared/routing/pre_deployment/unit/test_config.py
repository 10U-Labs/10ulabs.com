"""Tests for Terraform configuration files."""

from pathlib import Path


def test_config_file_exists_in_correct_location():
    """Verify that terraform.tfvars file exists."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent
    config_path = base / "src" / "api" / "backend" / "terraform.tfvars"
    file_exists = config_path.exists()
    assert file_exists


def test_config_has_aws_account_id(config):
    """Verify that config has AWS account ID."""
    has_aws_account_id = "aws_account_id" in config
    assert has_aws_account_id


def test_config_has_aws_region(config):
    """Verify that config has AWS region."""
    has_aws_region = "aws_region" in config
    assert has_aws_region


def test_shared_module_has_github_org():
    """Verify that shared module outputs.tf has github_org."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent
    outputs_path = base / "lib" / "terraform" / "modules" / "shared" / "outputs.tf"
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()
    has_github_org = 'github_org' in content
    assert has_github_org


def test_shared_module_has_github_repo():
    """Verify that shared module outputs.tf has github_repo."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent
    outputs_path = base / "lib" / "terraform" / "modules" / "shared" / "outputs.tf"
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()
    has_github_repo = 'name_for_github_repo' in content
    assert has_github_repo


def test_locals_tf_has_api_fqdn():
    """Verify that locals.tf has api_fqdn."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent
    locals_path = base / "src" / "api" / "backend" / "locals.tf"
    with open(locals_path, encoding="utf-8") as f:
        content = f.read()
    has_api_fqdn = 'api_fqdn' in content
    assert has_api_fqdn


def test_cloudfront_health_endpoint_path_pattern_exists():
    """Verify that CloudFront has health endpoint path pattern."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent
    cloudfront_file = base / "src" / "api" / "backend" / "cloudfront_s3.tf"
    with open(cloudfront_file, encoding="utf-8") as f:
        content = f.read()
    has_health_path_pattern = 'path_pattern           = "/health"' in content
    assert has_health_path_pattern


def test_cloudfront_health_endpoint_allows_options():
    """Verify that CloudFront health endpoint allows OPTIONS."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent
    cloudfront_file = base / "src" / "api" / "backend" / "cloudfront_s3.tf"
    with open(cloudfront_file, encoding="utf-8") as f:
        content = f.read()
    health_section_start = content.find('path_pattern           = "/health"')
    health_section = content[health_section_start:health_section_start + 500]
    allows_options = 'OPTIONS' in health_section
    assert allows_options
