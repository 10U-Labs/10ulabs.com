"""E2E tests for DNS resolution and domain functionality"""
import json
from pathlib import Path
import boto3
import dns.resolver
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def route53_client(config):
    """Create Route53 client"""
    return boto3.client('route53', region_name=config['aws_region'])


def test_hosted_zone_name_servers_resolve(route53_client, config):
    """Test that the hosted zone's name servers are functional"""
    domain_name = config['domain_name']

    # Get the hosted zone
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    assert zone is not None, f"Hosted zone for {domain_name} not found"

    # Get name servers
    ns_response = route53_client.get_hosted_zone(Id=zone['Id'])
    name_servers = ns_response['DelegationSet']['NameServers']

    assert len(name_servers) >= 4, "Should have at least 4 name servers"

    # Verify each name server responds
    for ns in name_servers:
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [ns]
            # Query for SOA record (should always exist)
            answers = resolver.resolve(domain_name, 'SOA')
            assert len(answers) > 0, f"Name server {ns} should respond to SOA query"
        except Exception as e:
            pytest.fail(f"Name server {ns} failed to respond: {e}")


def test_create_and_resolve_test_record(route53_client, config):
    """E2E test: Create a record and verify it resolves via DNS"""
    domain_name = config['domain_name']

    # Find the hosted zone
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    assert zone is not None

    # Get name servers for this zone
    ns_response = route53_client.get_hosted_zone(Id=zone['Id'])
    name_servers = ns_response['DelegationSet']['NameServers']

    # Create a test TXT record
    test_record_name = f"e2e-test.{domain_name}"
    test_value = "e2e-test-value-12345"

    try:
        # Create record
        route53_client.change_resource_record_sets(
            HostedZoneId=zone['Id'],
            ChangeBatch={
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': test_record_name,
                        'Type': 'TXT',
                        'TTL': 60,
                        'ResourceRecords': [{'Value': f'"{test_value}"'}]
                    }
                }]
            }
        )

        # Wait a moment for propagation
        import time
        time.sleep(2)

        # Resolve the record using the zone's name servers
        resolver = dns.resolver.Resolver()
        # Pick first name server
        resolver.nameservers = [dns.resolver.resolve(name_servers[0], 'A')[0].to_text()]

        answers = resolver.resolve(test_record_name, 'TXT')
        resolved_value = str(answers[0]).strip('"')

        assert resolved_value == test_value, f"Expected {test_value}, got {resolved_value}"

    finally:
        # Clean up - delete the test record
        try:
            route53_client.change_resource_record_sets(
                HostedZoneId=zone['Id'],
                ChangeBatch={
                    'Changes': [{
                        'Action': 'DELETE',
                        'ResourceRecordSet': {
                            'Name': test_record_name,
                            'Type': 'TXT',
                            'TTL': 60,
                            'ResourceRecords': [{'Value': f'"{test_value}"'}]
                        }
                    }]
                }
            )
        except:
            pass


def test_soa_record_exists(route53_client, config):
    """Test that SOA record exists for the domain"""
    domain_name = config['domain_name']

    # Find the hosted zone
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    assert zone is not None

    # Get records
    records = route53_client.list_resource_record_sets(HostedZoneId=zone['Id'])

    # Find SOA record
    soa_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'SOA':
            soa_record = record
            break

    assert soa_record is not None, "SOA record should exist"
    assert len(soa_record['ResourceRecords']) > 0, "SOA record should have values"


def test_ns_record_exists(route53_client, config):
    """Test that NS record exists for the domain"""
    domain_name = config['domain_name']

    # Find the hosted zone
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    assert zone is not None

    # Get records
    records = route53_client.list_resource_record_sets(HostedZoneId=zone['Id'])

    # Find NS record
    ns_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'NS' and record['Name'] == f"{domain_name}.":
            ns_record = record
            break

    assert ns_record is not None, "NS record should exist"
    assert len(ns_record['ResourceRecords']) >= 4, "Should have at least 4 name servers"
