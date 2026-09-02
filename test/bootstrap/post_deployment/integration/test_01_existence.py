from typing import Any, Dict, Optional

from test_fixtures.aws import iam_role_exists


def test_central_logs_bucket_exists(s3_client: Any, config: Dict[str, Any]) -> None:
    bucket_name = config['name_for_central_logs_bucket']
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_terraform_state_bucket_exists(s3_client: Any, config: Dict[str, Any]) -> None:
    bucket_name = config['name_for_terraform_state_bucket']
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_terraform_state_file_exists(s3_client: Any, config: Dict[str, Any]) -> None:
    bucket_name = config['name_for_terraform_state_bucket']
    s3_client.head_object(
        Bucket=bucket_name,
        Key='bootstrap/terraform.tfstate'
    )
    assert True


def test_cloudtrail_trail_exists(cloudtrail_client: Any) -> None:
    trails = cloudtrail_client.describe_trails()
    assert len(trails['trailList']) > 0


def test_cloudtrail_s3_bucket_exists(s3_client: Any, cloudtrail_client: Any) -> None:
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_cloudtrail_log_group_exists(logs_client: Any, cloudtrail_log_group_name: str) -> None:
    response = logs_client.describe_log_groups(logGroupNamePrefix=cloudtrail_log_group_name)
    assert len(response['logGroups']) > 0


def test_access_log_bucket_exists(s3_client: Any, access_log_bucket: Optional[str]) -> None:
    if access_log_bucket:
        head_response = s3_client.head_bucket(Bucket=access_log_bucket)
        assert head_response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_cloudwatch_logs_iam_role_exists(cloudtrail_client: Any, iam_client: Any) -> None:
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    if 'CloudWatchLogsRoleArn' in trail:
        role_name = trail['CloudWatchLogsRoleArn'].split('/')[-1]
        role = iam_client.get_role(RoleName=role_name)
        assert role['Role']['RoleName'] == role_name


def test_hosted_zone_exists(route53_client: Any, config: Dict[str, Any]) -> None:
    domain_name = config['domain_name']
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = zones['HostedZones'][0]
    assert zone['Name'] == f"{domain_name}."


def test_google_verification_txt_record_exists(txt_record: Any) -> None:
    assert txt_record is not None


def test_gmail_mx_record_exists(mx_record: Any) -> None:
    assert mx_record is not None


def test_iam_role_exists_in_aws(iam_client: Any, config: Dict[str, Any]) -> None:
    role_name = config['name_for_github_actions_role']
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


def test_github_actions_role_exists(iam_client: Any, config: Dict[str, Any]) -> None:
    role_name = config.get('name_for_github_actions_role', 'TenULabsGitHubActionsRole')
    assert iam_role_exists(iam_client, role_name), f"GitHub Actions role '{role_name}' missing"


def test_oidc_provider_exists_in_aws(iam_client: Any, aws_account_id: str) -> None:
    account_id = aws_account_id
    provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
    assert response['Url'] == 'token.actions.githubusercontent.com'


def test_github_pat_parameter_exists(ssm_client: Any, config: Dict[str, Any]) -> None:
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [config['ssm_parameter_name_for_github_pat']]}]
    )
    assert len(response['Parameters']) == 1


def test_github_app_id_parameter_exists(ssm_client: Any, config: Dict[str, Any]) -> None:
    param_name = f"{config['github_app_ssm_prefix']}/id"
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [param_name]}]
    )
    assert len(response['Parameters']) == 1


def test_github_app_installation_id_parameter_exists(
    ssm_client: Any,
    config: Dict[str, Any]
) -> None:
    param_name = f"{config['github_app_ssm_prefix']}/installation_id"
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [param_name]}]
    )
    assert len(response['Parameters']) == 1


def test_github_app_private_key_parameter_exists(ssm_client: Any, config: Dict[str, Any]) -> None:
    param_name = f"{config['github_app_ssm_prefix']}/private_key"
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [param_name]}]
    )
    assert len(response['Parameters']) == 1
