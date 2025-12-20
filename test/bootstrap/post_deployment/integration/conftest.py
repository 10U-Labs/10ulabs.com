"""Fixtures for bootstrap post-deployment integration tests."""
import pytest


@pytest.fixture(scope="module", name="cloudtrail_trail")
def cloudtrail_trail_fixture(cloudtrail_client):
    """Get the CloudTrail trail."""
    trails = cloudtrail_client.describe_trails()
    return trails['trailList'][0]


@pytest.fixture(scope="module", name="cloudtrail_log_group_name")
def cloudtrail_log_group_name_fixture(cloudtrail_trail):
    """Get the CloudTrail log group name."""
    log_group_arn = cloudtrail_trail['CloudWatchLogsLogGroupArn']
    return log_group_arn.split(':log-group:')[1].split(':')[0]


@pytest.fixture(scope="module", name="access_log_bucket")
def access_log_bucket_fixture(s3_client, cloudtrail_trail):
    """Get the access log bucket name."""
    cloudtrail_bucket_name = cloudtrail_trail['S3BucketName']
    response = s3_client.get_bucket_logging(Bucket=cloudtrail_bucket_name)
    if 'LoggingEnabled' in response:
        return response['LoggingEnabled']['TargetBucket']
    return None


@pytest.fixture(scope="module")
def txt_record(route53_client, hosted_zone, config):
    """Get the TXT record for the domain."""
    domain_name = config['domain_name']
    records = route53_client.list_resource_record_sets(
        HostedZoneId=hosted_zone['Id'],
        StartRecordName=f"{domain_name}.",
        StartRecordType='TXT'
    )
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'TXT' and record['Name'] == f"{domain_name}.":
            return record
    return None


@pytest.fixture(scope="module")
def mx_record(route53_client, hosted_zone, config):
    """Get the MX record for the domain."""
    domain_name = config['domain_name']
    records = route53_client.list_resource_record_sets(
        HostedZoneId=hosted_zone['Id'],
        StartRecordName=f"{domain_name}.",
        StartRecordType='MX'
    )
    for record in records['ResourceRecordSets']:
        if record['Type'] == 'MX' and record['Name'] == f"{domain_name}.":
            return record
    return None
