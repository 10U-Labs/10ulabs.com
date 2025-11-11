import json
from pathlib import Path
import boto3
import dns.resolver
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def route53_client(config):
    return boto3.client('route53', region_name=config['aws_region'])


def test_google_verification_record_resolves_via_public_dns(route53_client, config):
    domain_name = config['domain_name']
    google_verification = config['google_site_verification']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    zone_details = route53_client.get_hosted_zone(Id=zone['Id'])
    name_servers = zone_details['DelegationSet']['NameServers']

    ns_ip = dns.resolver.resolve(name_servers[0], 'A')[0].to_text()

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [ns_ip]

    try:
        answers = resolver.resolve(domain_name, 'TXT')
        txt_values = [str(rdata) for rdata in answers]

        expected_value = f'"google-site-verification={google_verification}"'
        assert any(expected_value in txt for txt in txt_values)
    except dns.resolver.NXDOMAIN:
        pytest.fail(f"Domain {domain_name} not found in DNS")
    except dns.resolver.NoAnswer:
        pytest.fail(f"No TXT records found for {domain_name}")


def test_google_verification_record_has_correct_content(route53_client, config):
    domain_name = config['domain_name']
    google_verification = config['google_site_verification']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    zone_details = route53_client.get_hosted_zone(Id=zone['Id'])
    name_servers = zone_details['DelegationSet']['NameServers']

    ns_ip = dns.resolver.resolve(name_servers[0], 'A')[0].to_text()

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [ns_ip]

    answers = resolver.resolve(domain_name, 'TXT')
    txt_values = [str(rdata).strip('"') for rdata in answers]

    expected_prefix = f"google-site-verification={google_verification}"
    assert any(expected_prefix in txt for txt in txt_values)
