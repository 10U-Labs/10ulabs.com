"""Post-deployment integration tests for domain hosted zone"""
import json
from pathlib import Path
import boto3
import pytest


@pytest.fixture
def config():
    """Load domain config"""
    config_path = Path(__file__).parents[4] / "config" / "cloudtrail_and_domain_name.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def route53_client(config):
    """Create Route53 client"""
    return boto3.client('route53', region_name=config['aws_region'])


def test_hosted_zone_exists(route53_client, config):
    domain_name = config['domain_name']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    assert zone is not None, f"Hosted zone for {domain_name} not found"


def test_hosted_zone_can_create_record(route53_client, config):
    domain_name = config['domain_name']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

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


def test_hosted_zone_id_export_exists(config):
    cf_client = boto3.client('cloudformation', region_name=config['aws_region'])

    domain_name = config['domain_name']
    normalized_domain = domain_name.replace('.', '-')
    expected_export = f"{normalized_domain}-HostedZoneId"

    exports = []
    paginator = cf_client.get_paginator('list_exports')
    for page in paginator.paginate():
        exports.extend(page['Exports'])

    export_names = [e['Name'] for e in exports]

    assert expected_export in export_names, f"Missing CloudFormation export: {expected_export}"


def test_hosted_zone_name_export_exists(config):
    cf_client = boto3.client('cloudformation', region_name=config['aws_region'])

    domain_name = config['domain_name']
    normalized_domain = domain_name.replace('.', '-')
    expected_export = f"{normalized_domain}-HostedZoneName"

    exports = []
    paginator = cf_client.get_paginator('list_exports')
    for page in paginator.paginate():
        exports.extend(page['Exports'])

    export_names = [e['Name'] for e in exports]

    assert expected_export in export_names, f"Missing CloudFormation export: {expected_export}"


def test_hosted_zone_is_discoverable(route53_client, config):
    domain_name = config['domain_name']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")

    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    assert zone is not None, "Hosted zone should be discoverable by other stacks"


def test_hosted_zone_has_id(route53_client, config):
    domain_name = config['domain_name']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")

    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    assert 'Id' in zone, "Hosted zone should have an ID for other stacks to reference"


def test_hosted_zone_is_public(route53_client, config):
    domain_name = config['domain_name']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")

    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    assert zone['Config']['PrivateZone'] == False, "Hosted zone should be public"


@pytest.fixture
def cloudtrail_client(config):
    """Create CloudTrail client"""
    return boto3.client('cloudtrail', region_name=config['aws_region'])


@pytest.fixture
def s3_client(config):
    """Create S3 client"""
    return boto3.client('s3', region_name=config['aws_region'])


@pytest.fixture
def logs_client(config):
    """Create CloudWatch Logs client"""
    return boto3.client('logs', region_name=config['aws_region'])


def test_cloudtrail_trail_exists(cloudtrail_client):
    """Test that CloudTrail trail exists"""
    trails = cloudtrail_client.describe_trails()
    assert len(trails['trailList']) > 0, "At least one CloudTrail trail should exist"


def test_cloudtrail_trail_is_multi_region(cloudtrail_client):
    """Test that CloudTrail trail is configured as multi-region"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert trail['IsMultiRegionTrail'] is True, "Trail should be multi-region"


def test_cloudtrail_includes_global_service_events(cloudtrail_client):
    """Test that CloudTrail includes global service events"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert trail['IncludeGlobalServiceEvents'] is True, "Trail should include global service events"


def test_cloudtrail_is_actively_logging(cloudtrail_client):
    """Test that CloudTrail is actively logging"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    status = cloudtrail_client.get_trail_status(Name=trail['TrailARN'])
    assert status['IsLogging'] is True, "Trail should be actively logging"


def test_cloudtrail_s3_bucket_exists(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket exists"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']

    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200, "S3 bucket should exist"


def test_cloudtrail_s3_bucket_has_encryption(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']

    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert 'ServerSideEncryptionConfiguration' in encryption, "Bucket should have encryption enabled"


def test_cloudtrail_s3_bucket_encryption_has_rules(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']

    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert 'Rules' in encryption['ServerSideEncryptionConfiguration'], "Bucket should have encryption rules"


def test_cloudtrail_s3_bucket_blocks_public_acls(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket blocks public ACLs"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']

    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    config = public_access['PublicAccessBlockConfiguration']
    assert config['BlockPublicAcls'] is True, "Bucket should block public ACLs"


def test_cloudtrail_s3_bucket_blocks_public_policy(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket blocks public policy"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']

    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    config = public_access['PublicAccessBlockConfiguration']
    assert config['BlockPublicPolicy'] is True, "Bucket should block public policies"


def test_cloudtrail_s3_bucket_ignores_public_acls(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket ignores public ACLs"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']

    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    config = public_access['PublicAccessBlockConfiguration']
    assert config['IgnorePublicAcls'] is True, "Bucket should ignore public ACLs"


def test_cloudtrail_s3_bucket_restricts_public_buckets(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket restricts public buckets"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']

    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    config = public_access['PublicAccessBlockConfiguration']
    assert config['RestrictPublicBuckets'] is True, "Bucket should restrict public buckets"


def test_cloudtrail_s3_bucket_versioning_disabled(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket has versioning disabled"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']

    try:
        versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
        assert versioning.get('Status') != 'Enabled', "Bucket should not have versioning enabled"
    except KeyError:
        pass


def test_cloudtrail_has_cloudwatch_logs_configured(cloudtrail_client):
    """Test that CloudTrail has CloudWatch Logs configured"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert 'CloudWatchLogsLogGroupArn' in trail, "Trail should have CloudWatch Logs configured"


def test_cloudtrail_log_group_exists(logs_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    log_group_arn = trail['CloudWatchLogsLogGroupArn']
    log_group_name = log_group_arn.split(':log-group:')[1].split(':')[0]

    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    assert len(response['logGroups']) > 0, "Log group should exist"


def test_cloudtrail_log_group_has_one_year_retention(logs_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    log_group_arn = trail['CloudWatchLogsLogGroupArn']
    log_group_name = log_group_arn.split(':log-group:')[1].split(':')[0]

    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_group = response['logGroups'][0]
    assert log_group['retentionInDays'] == 365, "Log group should have 1-year retention"


def test_cloudtrail_has_event_selectors_property(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    selectors = cloudtrail_client.get_event_selectors(TrailName=trail['Name'])
    assert 'EventSelectors' in selectors, "Trail should have event selectors"


def test_cloudtrail_has_at_least_one_event_selector(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    selectors = cloudtrail_client.get_event_selectors(TrailName=trail['Name'])
    assert len(selectors['EventSelectors']) > 0, "Trail should have at least one event selector"


def test_cloudtrail_captures_read_and_write_events(cloudtrail_client):
    """Test that CloudTrail captures both read and write events"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    selectors = cloudtrail_client.get_event_selectors(TrailName=trail['Name'])
    selector = selectors['EventSelectors'][0]
    assert selector['ReadWriteType'] == 'All', "Trail should capture both read and write events"


def test_cloudtrail_includes_management_events(cloudtrail_client):
    """Test that CloudTrail includes management events"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    selectors = cloudtrail_client.get_event_selectors(TrailName=trail['Name'])
    selector = selectors['EventSelectors'][0]
    assert selector['IncludeManagementEvents'] is True, "Trail should include management events"


def test_cloudtrail_writes_logs_to_s3(s3_client, cloudtrail_client):
    """Test that CloudTrail has successfully written logs to S3"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']

    objects = s3_client.list_objects_v2(
        Bucket=bucket_name,
        MaxKeys=10
    )
    assert objects.get('KeyCount', 0) > 0 or 'Contents' in objects, "CloudTrail should have written logs to S3"


def test_cloudtrail_writes_logs_to_cloudwatch(logs_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    log_group_arn = trail['CloudWatchLogsLogGroupArn']
    log_group_name = log_group_arn.split(':log-group:')[1].split(':')[0]

    streams = logs_client.describe_log_streams(
        logGroupName=log_group_name,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )
    assert len(streams['logStreams']) > 0, "CloudTrail should have created log streams in CloudWatch Logs"


@pytest.fixture
def hosted_zone(route53_client, config):
    domain_name = config['domain_name']
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            return z
    return None


def test_hosted_zone_exists(hosted_zone, config):
    assert hosted_zone is not None, f"Hosted zone for {config['domain_name']} not found"


def test_hosted_zone_has_minimum_nameservers(route53_client, hosted_zone):
    ns_response = route53_client.get_hosted_zone(Id=hosted_zone['Id'])
    name_servers = ns_response['DelegationSet']['NameServers']
    assert len(name_servers) >= 4, "Should have at least 4 name servers"


def test_soa_record_exists(route53_client, hosted_zone):
    records = route53_client.list_resource_record_sets(HostedZoneId=hosted_zone['Id'])
    soa_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'SOA':
            soa_record = record
            break
    assert soa_record is not None, "SOA record should exist"


def test_soa_record_has_values(route53_client, hosted_zone):
    records = route53_client.list_resource_record_sets(HostedZoneId=hosted_zone['Id'])
    soa_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'SOA':
            soa_record = record
            break
    assert len(soa_record['ResourceRecords']) > 0, "SOA record should have values"


def test_ns_record_exists(route53_client, hosted_zone, config):
    domain_name = config['domain_name']
    records = route53_client.list_resource_record_sets(HostedZoneId=hosted_zone['Id'])
    ns_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'NS' and record['Name'] == f"{domain_name}.":
            ns_record = record
            break
    assert ns_record is not None, "NS record should exist"


def test_ns_record_has_minimum_nameservers(route53_client, hosted_zone, config):
    domain_name = config['domain_name']
    records = route53_client.list_resource_record_sets(HostedZoneId=hosted_zone['Id'])
    ns_record = None
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'NS' and record['Name'] == f"{domain_name}.":
            ns_record = record
            break
    assert len(ns_record['ResourceRecords']) >= 4, "Should have at least 4 name servers"
