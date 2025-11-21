import boto3
import pytest


@pytest.fixture
def route53_client(config):
    return boto3.client('route53', region_name=config['aws']['region'])


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
    cf_client = boto3.client('cloudformation', region_name=config['aws']['region'])

    stacks = cf_client.describe_stacks()
    gmail_stack = None
    for stack in stacks['Stacks']:
        if 'gmail' in stack['StackName'].lower() and stack['StackStatus'] != 'DELETE_COMPLETE':
            gmail_stack = stack
            break

    assert gmail_stack is not None


def test_cloudformation_stack_is_not_in_failed_state(config):
    cf_client = boto3.client('cloudformation', region_name=config['aws']['region'])

    stacks = cf_client.describe_stacks()
    gmail_stack = None
    for stack in stacks['Stacks']:
        if 'gmail' in stack['StackName'].lower() and stack['StackStatus'] != 'DELETE_COMPLETE':
            gmail_stack = stack
            break

    if gmail_stack:
        assert 'FAILED' not in gmail_stack['StackStatus']


def test_stack_has_google_verification_output(config):
    cf_client = boto3.client('cloudformation', region_name=config['aws']['region'])

    stacks = cf_client.describe_stacks()
    gmail_stack = None
    for stack in stacks['Stacks']:
        if 'gmail' in stack['StackName'].lower() and stack['StackStatus'] != 'DELETE_COMPLETE':
            gmail_stack = stack
            break

    if gmail_stack:
        outputs = {o['OutputKey']: o['OutputValue'] for o in gmail_stack.get('Outputs', [])}
        assert 'GoogleVerificationRecord' in outputs or 'GoogleVerificationValue' in outputs


def test_gmail_mx_record_exists(route53_client, config):
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
        StartRecordType='MX'
    )

    mx_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'MX' and record['Name'] == f"{domain_name}.":
            mx_record = record
            break

    assert mx_record is not None


def test_gmail_mx_record_has_correct_priority(route53_client, config):
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
        StartRecordType='MX'
    )

    mx_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'MX' and record['Name'] == f"{domain_name}.":
            mx_record = record
            break

    record_values = [rr['Value'] for rr in mx_record['ResourceRecords']]
    assert any('1 smtp.google.com' in val for val in record_values)


def test_gmail_mx_record_has_ttl(route53_client, config):
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
        StartRecordType='MX'
    )

    mx_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'MX' and record['Name'] == f"{domain_name}.":
            mx_record = record
            break

    assert 'TTL' in mx_record


def test_txt_record_ttl_equals_300(route53_client, config):
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

    assert txt_record['TTL'] == 300


def test_mx_record_ttl_equals_300(route53_client, config):
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
        StartRecordType='MX'
    )

    mx_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'MX' and record['Name'] == f"{domain_name}.":
            mx_record = record
            break

    assert mx_record['TTL'] == 300


def test_mx_record_hostname_has_trailing_dot(route53_client, config):
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
        StartRecordType='MX'
    )

    mx_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'MX' and record['Name'] == f"{domain_name}.":
            mx_record = record
            break

    record_values = [rr['Value'] for rr in mx_record['ResourceRecords']]
    assert any('smtp.google.com.' in val for val in record_values)


def test_mx_record_priority_equals_one(route53_client, config):
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
        StartRecordType='MX'
    )

    mx_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'MX' and record['Name'] == f"{domain_name}.":
            mx_record = record
            break

    record_values = [rr['Value'] for rr in mx_record['ResourceRecords']]
    assert any(val.startswith('1 ') for val in record_values)


def test_cloudformation_outputs_have_correct_values(config):
    cf_client = boto3.client('cloudformation', region_name=config['aws']['region'])

    stacks = cf_client.describe_stacks()
    gmail_stack = None
    for stack in stacks['Stacks']:
        if 'gmail' in stack['StackName'].lower() and stack['StackStatus'] != 'DELETE_COMPLETE':
            gmail_stack = stack
            break

    if gmail_stack:
        outputs = {o['OutputKey']: o['OutputValue'] for o in gmail_stack.get('Outputs', [])}

        if 'GoogleVerificationValue' in outputs:
            assert f"google-site-verification={config['google_site_verification']}" in outputs['GoogleVerificationValue']

        if 'GoogleVerificationRecord' in outputs:
            assert config['domain_name'] in outputs['GoogleVerificationRecord']

        if 'GmailMxRecordOutput' in outputs:
            assert config['domain_name'] in outputs['GmailMxRecordOutput']
