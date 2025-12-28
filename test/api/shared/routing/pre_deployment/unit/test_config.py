"""Tests for Terraform configuration files."""

from repo_utils import REPO_ROOT

ROUTING_DIR = REPO_ROOT / "src" / "api" / "shared" / "routing"
SHARED_MODULE_DIR = REPO_ROOT / "lib" / "terraform" / "modules" / "shared"


def test_config_file_exists_in_correct_location():
    """Verify that terraform.tfvars file exists."""
    config_path = ROUTING_DIR / "terraform.tfvars"
    assert config_path.exists()


def test_config_has_aws_account_id(config):
    """Verify that config has AWS account ID."""
    assert "aws_account_id" in config


def test_config_has_aws_region(config):
    """Verify that config has AWS region."""
    assert "aws_region" in config


def test_shared_module_has_github_org():
    """Verify that shared module outputs.tf has github_org."""
    outputs_path = SHARED_MODULE_DIR / "outputs.tf"
    content = outputs_path.read_text(encoding="utf-8")
    assert 'github_org' in content


def test_shared_module_has_github_repo():
    """Verify that shared module outputs.tf has github_repo."""
    outputs_path = SHARED_MODULE_DIR / "outputs.tf"
    content = outputs_path.read_text(encoding="utf-8")
    assert 'name_for_github_repo' in content


def test_locals_tf_has_api_fqdn():
    """Verify that locals.tf has api_fqdn."""
    locals_path = ROUTING_DIR / "locals.tf"
    content = locals_path.read_text(encoding="utf-8")
    assert 'api_fqdn' in content


def test_cloudfront_health_endpoint_path_pattern_exists():
    """Verify that CloudFront has health endpoint path pattern."""
    cloudfront_file = ROUTING_DIR / "cloudfront_s3.tf"
    content = cloudfront_file.read_text(encoding="utf-8")
    assert 'path_pattern           = "/health"' in content


def test_cloudfront_health_endpoint_allows_options():
    """Verify that CloudFront health endpoint allows OPTIONS."""
    cloudfront_file = ROUTING_DIR / "cloudfront_s3.tf"
    content = cloudfront_file.read_text(encoding="utf-8")
    health_section_start = content.find('path_pattern           = "/health"')
    health_section = content[health_section_start:health_section_start + 500]
    assert 'OPTIONS' in health_section
