"""Post-deployment integration tests for domain hosted zone"""
import json
from pathlib import Path
import boto3
import pytest


@pytest.fixture
def config():
    """Load domain config"""
    config_path = Path(__file__).parents[4] / "src" / "domain-name" / "config.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def route53_client(config):
    """Create Route53 client"""
    return boto3.client('route53', region_name=config['aws_region'])


def test_hosted_zone_can_create_record(route53_client, config):
    """Test that we can create a record in the hosted zone"""
    domain_name = config['domain_name']

    # Find the hosted zone
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    assert zone is not None, f"Hosted zone for {domain_name} not found"

    # Try to create a test record
    test_record = f"integration-test.{domain_name}"

    try:
        response = route53_client.change_resource_record_sets(
            HostedZoneId=zone['Id'],
            ChangeBatch={
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': test_record,
                        'Type': 'TXT',
                        'TTL': 60,
                        'ResourceRecords': [{'Value': '"integration-test"'}]
                    }
                }]
            }
        )

        assert response['ResponseMetadata']['HTTPStatusCode'] == 200

        # Clean up - delete the test record
        route53_client.change_resource_record_sets(
            HostedZoneId=zone['Id'],
            ChangeBatch={
                'Changes': [{
                    'Action': 'DELETE',
                    'ResourceRecordSet': {
                        'Name': test_record,
                        'Type': 'TXT',
                        'TTL': 60,
                        'ResourceRecords': [{'Value': '"integration-test"'}]
                    }
                }]
            }
        )

    except Exception as e:
        pytest.fail(f"Failed to create test record: {e}")


def test_hosted_zone_exports_are_usable(config):
    """Test that CloudFormation exports from domain stack are available"""
    cf_client = boto3.client('cloudformation', region_name=config['aws_region'])

    domain_name = config['domain_name']
    expected_exports = [
        f"{domain_name}-HostedZoneId",
        f"{domain_name}-HostedZoneName"
    ]

    # List all exports
    exports = []
    paginator = cf_client.get_paginator('list_exports')
    for page in paginator.paginate():
        exports.extend(page['Exports'])

    export_names = [e['Name'] for e in exports]

    for expected_export in expected_exports:
        assert expected_export in export_names, f"Missing CloudFormation export: {expected_export}"


def test_other_stacks_can_import_hosted_zone(route53_client, config):
    """Test that other stacks can successfully reference the hosted zone"""
    domain_name = config['domain_name']

    # Verify we can look up the zone (simulating what other stacks would do)
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")

    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    assert zone is not None, "Hosted zone should be discoverable by other stacks"
    assert 'Id' in zone, "Hosted zone should have an ID for other stacks to reference"
    assert zone['Config']['PrivateZone'] == False, "Hosted zone should be public"
