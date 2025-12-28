"""Pytest fixtures for www shared tests."""
from typing import Dict

import boto3
import pytest
from repo_utils import REPO_ROOT
from test_fixtures.config import create_website_config


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
    locals_path = REPO_ROOT / "src" / "www" / "shared" / "locals.tf"
    hosted_zone_id = _get_hosted_zone_id(shared_config.get('domain_name', ''))
    return create_website_config(locals_path, shared_config, hosted_zone_id)


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
