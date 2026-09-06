from typing import Any, Dict, Optional

import pytest

from test_fixtures.aws import find_lifecycle_rule


@pytest.fixture(scope="module", name="cloudtrail_trail")
def cloudtrail_trail_fixture(cloudtrail_client: Any) -> Any:
    trails = cloudtrail_client.describe_trails()
    return trails['trailList'][0]


@pytest.fixture(scope="module")
def cloudtrail_log_group_name(cloudtrail_trail: Any) -> str:
    log_group_arn = cloudtrail_trail['CloudWatchLogsLogGroupArn']
    return log_group_arn.split(':log-group:')[1].split(':')[0]


@pytest.fixture(scope="module")
def access_log_bucket(s3_client: Any, cloudtrail_trail: Any) -> Optional[str]:
    cloudtrail_bucket_name = cloudtrail_trail['S3BucketName']
    response = s3_client.get_bucket_logging(Bucket=cloudtrail_bucket_name)
    if 'LoggingEnabled' in response:
        return response['LoggingEnabled']['TargetBucket']
    return None


@pytest.fixture(scope="module")
def txt_record(route53_client: Any, hosted_zone: Any, config: Dict[str, Any]) -> Any:
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
def mx_record(route53_client: Any, hosted_zone: Any, config: Dict[str, Any]) -> Any:
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


@pytest.fixture(scope="module")
def delete_marker_rule(s3_client: Any, config: Dict[str, Any]) -> Dict[str, Any]:
    bucket_name = config['name_for_terraform_state_bucket']
    return find_lifecycle_rule(s3_client, bucket_name, 'expire-delete-markers') or {}


def _parameter_tags(ssm_client: Any, parameter_name: str) -> Dict[str, str]:
    response = ssm_client.list_tags_for_resource(
        ResourceType='Parameter',
        ResourceId=parameter_name
    )
    return {tag['Key']: tag['Value'] for tag in response['TagList']}


@pytest.fixture(scope="module")
def github_app_id_tags(ssm_client: Any, config: Dict[str, Any]) -> Dict[str, str]:
    return _parameter_tags(ssm_client, f"{config['github_app_ssm_prefix']}/id")


@pytest.fixture(scope="module")
def github_app_installation_id_tags(ssm_client: Any, config: Dict[str, Any]) -> Dict[str, str]:
    return _parameter_tags(ssm_client, f"{config['github_app_ssm_prefix']}/installation_id")


@pytest.fixture(scope="module")
def github_app_private_key_tags(ssm_client: Any, config: Dict[str, Any]) -> Dict[str, str]:
    return _parameter_tags(ssm_client, f"{config['github_app_ssm_prefix']}/private_key")
