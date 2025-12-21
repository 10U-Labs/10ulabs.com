"""Layer 1: Existence tests for bootstrap post-deployment.

These tests verify that resources were created by Terraform.
Tests are organized by resource domain for readability.
"""
import boto3
from botocore.exceptions import ClientError
import pytest

pytestmark = pytest.mark.layer(1)


# =============================================================================
# S3 Buckets
# =============================================================================


def test_central_logs_bucket_exists(s3_client, config):
    """Test that central logs bucket exists."""
    bucket_name = config['name_for_central_logs_bucket']
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_terraform_state_exists(config):
    """Test that Terraform state file exists in S3."""
    s3_client = boto3.client('s3', region_name=config['aws_region'])

    try:
        s3_client.head_object(
            Bucket='10ulabs-terraform-state-us-east-2',
            Key='bootstrap/terraform.tfstate'
        )
        state_exists = True
    except ClientError:
        state_exists = False

    assert state_exists


# =============================================================================
# CloudTrail
# =============================================================================


def test_cloudtrail_trail_exists(cloudtrail_client):
    """Test that CloudTrail trail exists."""
    trails = cloudtrail_client.describe_trails()
    assert len(trails['trailList']) > 0


def test_cloudtrail_s3_bucket_exists(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket exists."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_cloudtrail_log_group_exists(logs_client, cloudtrail_log_group_name):
    """Test that CloudTrail log group exists."""
    response = logs_client.describe_log_groups(logGroupNamePrefix=cloudtrail_log_group_name)
    assert len(response['logGroups']) > 0


def test_access_log_bucket_exists(s3_client, access_log_bucket):
    """Test that access log bucket exists."""
    if access_log_bucket:
        head_response = s3_client.head_bucket(Bucket=access_log_bucket)
        assert head_response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_cloudwatch_logs_iam_role_exists(cloudtrail_client, iam_client):
    """Test that CloudWatch Logs IAM role exists for CloudTrail."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    if 'CloudWatchLogsRoleArn' in trail:
        role_name = trail['CloudWatchLogsRoleArn'].split('/')[-1]
        role = iam_client.get_role(RoleName=role_name)
        assert role['Role']['RoleName'] == role_name


# =============================================================================
# Route53 / DNS
# =============================================================================


def test_hosted_zone_exists(route53_client, config):
    """Test that hosted zone exists in Route53."""
    domain_name = config['domain_name']
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = zones['HostedZones'][0]
    assert zone['Name'] == f"{domain_name}."


def test_google_verification_txt_record_exists(txt_record):
    """Test that Google verification TXT record exists."""
    assert txt_record is not None


def test_gmail_mx_record_exists(mx_record):
    """Test that Gmail MX record exists."""
    assert mx_record is not None


# =============================================================================
# IAM
# =============================================================================


def test_iam_role_exists_in_aws(iam_client, config):
    """Test that GitHub Actions IAM role exists in AWS."""
    role_name = config['name_for_github_actions_role']
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


def test_github_actions_role_exists(iam_client, config):
    """Verify GitHub Actions IAM role exists."""
    role_name = config.get('name_for_github_actions_role', 'TenULabsGitHubActionsRole')
    try:
        iam_client.get_role(RoleName=role_name)
    except iam_client.exceptions.NoSuchEntityException:
        pytest.fail(f"IAM role '{role_name}' does not exist")


# =============================================================================
# OIDC
# =============================================================================


def test_oidc_provider_exists_in_aws(iam_client, config):
    """Test that OIDC provider exists in AWS."""
    account_id = config['aws_account_id']
    provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
    assert response['Url'] == 'token.actions.githubusercontent.com'


# =============================================================================
# SSM
# =============================================================================


def test_github_pat_parameter_exists(ssm_client, config):
    """Test that GitHub PAT parameter exists in SSM."""
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [config['ssm_parameter_name_for_github_pat']]}]
    )
    assert len(response['Parameters']) == 1
