"""Pytest fixtures for www shared tests."""
from typing import Dict

import boto3
import pytest
from repo_utils import REPO_ROOT
from test_fixtures.config import parse_locals_file


def _parse_website_locals(shared_config: Dict[str, str]) -> Dict[str, str]:
    """Parse website locals from Terraform."""
    locals_path = REPO_ROOT / "src" / "www" / "shared" / "locals.tf"
    config = parse_locals_file(locals_path, shared_config)
    config['www_fqdn'] = f"www.{shared_config.get('domain_name', '')}"
    config['apex_fqdn'] = shared_config.get('domain_name', '')
    domain_name = shared_config.get('domain_name', '')
    config['website_bucket_name'] = f"www-{domain_name.replace('.', '-')}"
    github_org = shared_config.get('github_org', '')
    github_repo = shared_config.get('name_for_github_repo', '')
    config['github_repo_full'] = f"{github_org}/{github_repo}"
    return config


def _get_hosted_zone_id(domain_name: str) -> str:
    """Look up Route53 hosted zone ID for a domain."""
    route53 = boto3.client("route53")
    response = route53.list_hosted_zones_by_name(DNSName=domain_name, MaxItems="1")
    zones = response.get("HostedZones", [])
    for zone in zones:
        zone_name = zone["Name"].rstrip(".")
        if zone_name == domain_name:
            return zone["Id"].replace("/hostedzone/", "")
    return ""


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Provide website configuration for tests."""
    website_locals = _parse_website_locals(shared_config)
    result = {}
    result['aws_region'] = shared_config['aws_region']
    result['aws_account_id'] = website_locals.get('aws_account_id', '')
    result['central_logs_bucket'] = shared_config.get('name_for_central_logs_bucket', '')
    result['website_fqdn'] = website_locals.get('www_fqdn', '')
    result['website_bucket_name'] = website_locals.get('website_bucket_name', '')
    result['apex_fqdn'] = website_locals.get('apex_fqdn', '')
    result['github_org'] = shared_config.get('github_org', '')
    result['github_repo'] = website_locals.get('github_repo_full', '')
    result['resource_prefix'] = website_locals.get('resource_prefix', '')
    result['hosted_zone_id'] = _get_hosted_zone_id(shared_config.get('domain_name', ''))
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
