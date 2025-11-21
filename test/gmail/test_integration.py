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


def test_terraform_state_exists(config):
    s3_client = boto3.client('s3', region_name=config['aws']['region'])

    try:
        s3_client.head_object(
            Bucket='10ulabs-terraform-state',
            Key='gmail/terraform.tfstate'
        )
        state_exists = True
    except:
        state_exists = False

    assert state_exists
