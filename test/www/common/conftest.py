from typing import Dict

import boto3
import pytest
from repo_utils import REPO_ROOT
from test_fixtures.config import create_website_config


def _get_hosted_zone_id(domain_name: str) -> str:
    route53 = boto3.client("route53")
    response = route53.list_hosted_zones_by_name(DNSName=domain_name, MaxItems="1")
    zones = response.get("HostedZones", [])
    for zone in zones:
        zone_name = zone["Name"].rstrip(".")
        if zone_name == domain_name:
            return zone["Id"].replace("/hostedzone/", "")
    return ""


@pytest.fixture(scope="module")
def config(shared_config) -> Dict[str, str]:
    locals_path = REPO_ROOT / "src" / "www" / "common" / "locals.tf"
    hosted_zone_id = _get_hosted_zone_id(shared_config.get('domain_name', ''))
    return create_website_config(locals_path, shared_config, hosted_zone_id)


@pytest.fixture(name="website_src_path")
def fixture_website_src_path():
    return REPO_ROOT / "src" / "www" / "common"


@pytest.fixture
def cloudfront_s3_tf_content(website_src_path):
    with open(website_src_path / "cloudfront_s3.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def certificate_dns_tf_content(website_src_path):
    with open(website_src_path / "certificate_dns.tf", encoding="utf-8") as f:
        return f.read()
