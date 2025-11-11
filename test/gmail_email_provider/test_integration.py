import json
from pathlib import Path
import boto3
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def route53_client(config):
    return boto3.client('route53', region_name=config['aws_region'])


def test_google_verification_txt_record_exists(route53_client, config):
    domain_name = config['domain_name']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    assert zone is not None

    records = route53_client.list_resource_record_sets(
        HostedZoneId=zone['Id'],
        StartRecordName=f"{domain_name}.",
        StartRecordType='TXT'
    )

    txt_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'TXT' and record['Name'] == f"{domain_name}.":
            txt_record = record
            break

    assert txt_record is not None


def test_google_verification_txt_record_has_correct_value(route53_client, config):
    domain_name = config['domain_name']
    google_verification = config['google_site_verification']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    records = route53_client.list_resource_record_sets(
        HostedZoneId=zone['Id'],
        StartRecordName=f"{domain_name}.",
        StartRecordType='TXT'
    )

    txt_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'TXT' and record['Name'] == f"{domain_name}.":
            txt_record = record
            break

    expected_value = f'"google-site-verification={google_verification}"'
    record_values = [rr['Value'] for rr in txt_record['ResourceRecords']]
    assert expected_value in record_values


def test_google_verification_txt_record_has_ttl(route53_client, config):
    domain_name = config['domain_name']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    records = route53_client.list_resource_record_sets(
        HostedZoneId=zone['Id'],
        StartRecordName=f"{domain_name}.",
        StartRecordType='TXT'
    )

    txt_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'TXT' and record['Name'] == f"{domain_name}.":
            txt_record = record
            break

    assert 'TTL' in txt_record


def test_cloudformation_stack_exists(config):
    cf_client = boto3.client('cloudformation', region_name=config['aws_region'])

    stacks = cf_client.describe_stacks()
    gmail_stack = None
    for stack in stacks['Stacks']:
        if 'gmail' in stack['StackName'].lower() and stack['StackStatus'] != 'DELETE_COMPLETE':
            gmail_stack = stack
            break

    assert gmail_stack is not None


def test_cloudformation_stack_is_not_in_failed_state(config):
    cf_client = boto3.client('cloudformation', region_name=config['aws_region'])

    stacks = cf_client.describe_stacks()
    gmail_stack = None
    for stack in stacks['Stacks']:
        if 'gmail' in stack['StackName'].lower() and stack['StackStatus'] != 'DELETE_COMPLETE':
            gmail_stack = stack
            break

    if gmail_stack:
        assert 'FAILED' not in gmail_stack['StackStatus']


def test_stack_has_google_verification_output(config):
    cf_client = boto3.client('cloudformation', region_name=config['aws_region'])

    stacks = cf_client.describe_stacks()
    gmail_stack = None
    for stack in stacks['Stacks']:
        if 'gmail' in stack['StackName'].lower() and stack['StackStatus'] != 'DELETE_COMPLETE':
            gmail_stack = stack
            break

    if gmail_stack:
        outputs = {o['OutputKey']: o['OutputValue'] for o in gmail_stack.get('Outputs', [])}
        assert 'GoogleVerificationRecord' in outputs or 'GoogleVerificationValue' in outputs
