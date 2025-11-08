"""Post-deployment integration tests for domain hosted zone"""
import json
from pathlib import Path
import boto3
import pytest


@pytest.fixture
def config():
    """Load domain config"""
    config_path = Path(__file__).parents[4] / "src" / "foundational_infrastructure" / "config.json"
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


def test_cloudtrail_trail_exists_and_is_logging(cloudtrail_client):
    """Test that CloudTrail trail exists and is actively logging"""
    trails = cloudtrail_client.describe_trails()

    assert len(trails['trailList']) > 0, "At least one CloudTrail trail should exist"

    trail = trails['trailList'][0]
    assert trail['IsMultiRegionTrail'] is True, "Trail should be multi-region"
    assert trail['IncludeGlobalServiceEvents'] is True, "Trail should include global service events"

    status = cloudtrail_client.get_trail_status(Name=trail['TrailARN'])
    assert status['IsLogging'] is True, "Trail should be actively logging"


def test_cloudtrail_s3_bucket_exists_and_is_secure(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket exists and has proper security settings"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']

    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200, "S3 bucket should exist"

    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert 'Rules' in encryption, "Bucket should have encryption enabled"

    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    config = public_access['PublicAccessBlockConfiguration']
    assert config['BlockPublicAcls'] is True, "Bucket should block public ACLs"
    assert config['BlockPublicPolicy'] is True, "Bucket should block public policies"
    assert config['IgnorePublicAcls'] is True, "Bucket should ignore public ACLs"
    assert config['RestrictPublicBuckets'] is True, "Bucket should restrict public buckets"

    try:
        versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
        assert versioning.get('Status') != 'Enabled', "Bucket should not have versioning enabled"
    except KeyError:
        pass


def test_cloudtrail_log_group_exists(logs_client, cloudtrail_client):
    """Test that CloudWatch Logs log group for CloudTrail exists"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]

    assert 'CloudWatchLogsLogGroupArn' in trail, "Trail should have CloudWatch Logs configured"

    log_group_arn = trail['CloudWatchLogsLogGroupArn']
    log_group_name = log_group_arn.split(':')[-1].replace('log-group:', '').split(':')[0]

    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)

    assert len(response['logGroups']) > 0, "Log group should exist"
    log_group = response['logGroups'][0]
    assert log_group['retentionInDays'] == 365, "Log group should have 1-year retention"


def test_cloudtrail_event_selectors_capture_all_events(cloudtrail_client):
    """Test that CloudTrail is configured to capture all management events"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]

    selectors = cloudtrail_client.get_event_selectors(TrailName=trail['Name'])

    assert 'EventSelectors' in selectors, "Trail should have event selectors"
    assert len(selectors['EventSelectors']) > 0, "Trail should have at least one event selector"

    selector = selectors['EventSelectors'][0]
    assert selector['ReadWriteType'] == 'All', "Trail should capture both read and write events"
    assert selector['IncludeManagementEvents'] is True, "Trail should include management events"


def test_cloudtrail_can_write_to_s3_and_logs(cloudtrail_client, s3_client, logs_client):
    """Test that CloudTrail has successfully written logs to both S3 and CloudWatch Logs"""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']

    objects = s3_client.list_objects_v2(
        Bucket=bucket_name,
        MaxKeys=10
    )

    assert objects.get('KeyCount', 0) > 0 or 'Contents' in objects, "CloudTrail should have written logs to S3"

    log_group_arn = trail['CloudWatchLogsLogGroupArn']
    log_group_name = log_group_arn.split(':')[-1].replace('log-group:', '').split(':')[0]

    streams = logs_client.describe_log_streams(
        logGroupName=log_group_name,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )

    assert len(streams['logStreams']) > 0, "CloudTrail should have created log streams in CloudWatch Logs"
