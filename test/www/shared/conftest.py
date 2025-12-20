"""Pytest fixtures for www shared tests."""
import re
from typing import Dict

import pytest
from repo_utils import REPO_ROOT



def _parse_website_locals(shared_config: Dict[str, str]) -> Dict[str, str]:
    """Parse website locals from Terraform."""
    locals_path = REPO_ROOT / "src" / "www" / "shared" / "locals.tf"
    config = {}
    with open(locals_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#') and not line.startswith('locals'):
                if match := re.match(r'(\w+)\s*=\s*(.+)', line):
                    key, value = match.groups()
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        config[key] = value[1:-1]
                    elif 'module.shared.' in value:
                        ref = value.replace('module.shared.', '').strip()
                        config[key] = shared_config.get(ref, '')
    config['www_fqdn'] = f"www.{shared_config.get('domain_name', '')}"
    config['apex_fqdn'] = shared_config.get('domain_name', '')
    domain_name = shared_config.get('domain_name', '')
    config['website_bucket_name'] = f"www-{domain_name.replace('.', '-')}"
    github_org = shared_config.get('github_org', '')
    github_repo = shared_config.get('name_for_github_repo', '')
    config['github_repo_full'] = f"{github_org}/{github_repo}"
    return config


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Provide website configuration for tests."""
    website_locals = _parse_website_locals(shared_config)
    result = {}
    result['aws_region'] = website_locals.get('aws_region', '')
    result['aws_account_id'] = website_locals.get('aws_account_id', '')
    result['central_logs_bucket'] = shared_config.get('name_for_central_logs_bucket', '')
    result['website_fqdn'] = website_locals.get('www_fqdn', '')
    result['website_bucket_name'] = website_locals.get('website_bucket_name', '')
    result['apex_fqdn'] = website_locals.get('apex_fqdn', '')
    result['github_org'] = shared_config.get('github_org', '')
    result['github_repo'] = website_locals.get('github_repo_full', '')
    result['resource_prefix'] = website_locals.get('resource_prefix', '')
    return result


@pytest.fixture(name="website_src_path")
def fixture_website_src_path():
    """Provide path to website source directory."""
    return REPO_ROOT / "src" / "www" / "shared"


@pytest.fixture(name="cloudfront_s3_tf_content")
def fixture_cloudfront_s3_tf_content(website_src_path):
    """Provide CloudFront S3 Terraform file content."""
    with open(website_src_path / "cloudfront_s3.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(name="certificate_dns_tf_content")
def fixture_certificate_dns_tf_content(website_src_path):
    """Provide certificate DNS Terraform file content."""
    with open(website_src_path / "certificate_dns.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(name="contact_form_tf_content")
def fixture_contact_form_tf_content(website_src_path):
    """Provide contact form Terraform file content."""
    with open(website_src_path / "contact_form.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(name="contact_lambda_content")
def fixture_contact_lambda_content(website_src_path):
    """Provide contact Lambda file content."""
    with open(website_src_path / "lambdas" / "contact.py", encoding="utf-8") as f:
        return f.read()
