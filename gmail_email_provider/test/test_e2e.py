import json
from pathlib import Path
import boto3
import dns.resolver
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parents[1] / "config.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def route53_client(config):
    return boto3.client('route53', region_name=config['aws']['region'])


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


def test_mx_record_resolves_via_public_dns(route53_client, config):
    domain_name = config['domain_name']

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
        answers = resolver.resolve(domain_name, 'MX')
        assert len(answers) > 0
    except dns.resolver.NXDOMAIN:
        pytest.fail(f"Domain {domain_name} not found in DNS")
    except dns.resolver.NoAnswer:
        pytest.fail(f"No MX records found for {domain_name}")


def test_mx_record_returns_correct_priority_via_dns(route53_client, config):
    domain_name = config['domain_name']

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

    answers = resolver.resolve(domain_name, 'MX')
    priorities = [rdata.preference for rdata in answers]
    assert 1 in priorities


def test_mx_record_returns_smtp_hostname_via_dns(route53_client, config):
    domain_name = config['domain_name']

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

    answers = resolver.resolve(domain_name, 'MX')
    exchanges = [str(rdata.exchange) for rdata in answers]
    assert any('smtp.google.com' in exchange for exchange in exchanges)


def test_mx_record_has_correct_ttl_in_dns_response(route53_client, config):
    domain_name = config['domain_name']

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

    answers = resolver.resolve(domain_name, 'MX')
    assert answers.rrset.ttl == 300


def test_txt_record_has_correct_ttl_in_dns_response(route53_client, config):
    domain_name = config['domain_name']

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
    assert answers.rrset.ttl == 300
