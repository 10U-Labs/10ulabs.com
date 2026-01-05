"""Layer 2: Configuration tests for bootstrap post-deployment.

These tests verify that resources are configured correctly.
Tests assume Layer 1 existence tests have passed.
"""
import json
import pytest

from naming_conventions import validate_name
from test_fixtures.integration import assert_iam_role_name_is_pascalcase



# =============================================================================
# Fixtures for tfstate access
# =============================================================================


def find_tfstate_resource(state, resource_type, resource_name):
    """Find a resource in Terraform state by type and name."""
    for resource in state['resources']:
        if resource['type'] == resource_type and resource['name'] == resource_name:
            return resource['instances'][0]['attributes']
    return None


@pytest.fixture(name='tfstate')
def tfstate_fixture(s3_client, config):
    """Load Terraform state from S3."""
    response = s3_client.get_object(
        Bucket=config['name_for_terraform_state_bucket'],
        Key='bootstrap/terraform.tfstate'
    )
    return json.loads(response['Body'].read().decode('utf-8'))


@pytest.fixture(name='terraform_state_bucket_attrs')
def terraform_state_bucket_attrs_fixture(tfstate):
    """Get terraform state bucket attributes from tfstate."""
    return find_tfstate_resource(tfstate, 'aws_s3_bucket', 'terraform_state')


@pytest.fixture(name='central_logs_bucket_attrs')
def central_logs_bucket_attrs_fixture(tfstate):
    """Get central logs bucket attributes from tfstate."""
    return find_tfstate_resource(tfstate, 'aws_s3_bucket', 'central_logs')


# =============================================================================
# Central Logs Bucket Configuration
# =============================================================================


def test_central_logs_bucket_has_encryption(s3_client, config):
    """Test that central logs bucket has encryption enabled."""
    bucket_name = config['name_for_central_logs_bucket']
    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert 'ServerSideEncryptionConfiguration' in encryption


def test_central_logs_bucket_encryption_is_aes256(s3_client, config):
    """Test that central logs bucket uses AES256 encryption."""
    bucket_name = config['name_for_central_logs_bucket']
    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    rules = encryption['ServerSideEncryptionConfiguration']['Rules']
    algorithm = rules[0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
    assert algorithm == 'AES256'


def test_central_logs_bucket_blocks_public_acls(s3_client, config):
    """Test that central logs bucket blocks public ACLs."""
    bucket_name = config['name_for_central_logs_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['BlockPublicAcls'] is True


def test_central_logs_bucket_blocks_public_policy(s3_client, config):
    """Test that central logs bucket blocks public policy."""
    bucket_name = config['name_for_central_logs_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['BlockPublicPolicy'] is True


def test_central_logs_bucket_ignores_public_acls(s3_client, config):
    """Test that central logs bucket ignores public ACLs."""
    bucket_name = config['name_for_central_logs_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['IgnorePublicAcls'] is True


def test_central_logs_bucket_restricts_public_buckets(s3_client, config):
    """Test that central logs bucket restricts public buckets."""
    bucket_name = config['name_for_central_logs_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['RestrictPublicBuckets'] is True


def test_central_logs_bucket_versioning_disabled(s3_client, config):
    """Test that central logs bucket has versioning disabled."""
    bucket_name = config['name_for_central_logs_bucket']
    versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert versioning.get('Status') != 'Enabled'


def test_central_logs_bucket_has_log_delivery_write_acl(s3_client, config):
    """Test that central logs bucket has log-delivery-write ACL."""
    bucket_name = config['name_for_central_logs_bucket']
    acl = s3_client.get_bucket_acl(Bucket=bucket_name)
    grantees = [g['Grantee'].get('URI', '') for g in acl.get('Grants', [])]
    log_delivery_uri = 'http://acs.amazonaws.com/groups/s3/LogDelivery'
    assert any(log_delivery_uri in g for g in grantees)


def test_central_logs_bucket_ownership_is_bucket_owner_preferred(s3_client, config):
    """Test that central logs bucket ownership is BucketOwnerPreferred."""
    bucket_name = config['name_for_central_logs_bucket']
    ownership = s3_client.get_bucket_ownership_controls(Bucket=bucket_name)
    rules = ownership['OwnershipControls']['Rules']
    assert rules[0]['ObjectOwnership'] == 'BucketOwnerPreferred'


def test_central_logs_bucket_has_lifecycle_configuration(s3_client, config):
    """Test that central logs bucket has lifecycle configuration."""
    bucket_name = config['name_for_central_logs_bucket']
    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    assert 'Rules' in lifecycle


def test_central_logs_bucket_has_standard_ia_transition(s3_client, config):
    """Test that central logs bucket has Standard-IA transition."""
    bucket_name = config['name_for_central_logs_bucket']
    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    rule = lifecycle['Rules'][0]
    storage_classes = [t['StorageClass'] for t in rule['Transitions']]
    assert 'STANDARD_IA' in storage_classes


def test_central_logs_bucket_has_glacier_transition(s3_client, config):
    """Test that central logs bucket has Glacier transition."""
    bucket_name = config['name_for_central_logs_bucket']
    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    rule = lifecycle['Rules'][0]
    storage_classes = [t['StorageClass'] for t in rule['Transitions']]
    assert 'GLACIER' in storage_classes


def test_central_logs_bucket_has_expiration(s3_client, config):
    """Test that central logs bucket has expiration configured."""
    bucket_name = config['name_for_central_logs_bucket']
    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    rule = lifecycle['Rules'][0]
    assert 'Expiration' in rule


def test_central_logs_bucket_has_policy(s3_client, config):
    """Test that central logs bucket has a bucket policy."""
    bucket_name = config['name_for_central_logs_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    assert 'Policy' in policy


def test_central_logs_bucket_policy_denies_insecure_transport(s3_client, config):
    """Test that central logs bucket policy denies insecure transport."""
    bucket_name = config['name_for_central_logs_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    assert 'aws:SecureTransport' in policy_doc


def test_central_logs_bucket_has_logging_enabled(s3_client, config):
    """Test that central logs bucket has logging enabled."""
    bucket_name = config['name_for_central_logs_bucket']
    logging = s3_client.get_bucket_logging(Bucket=bucket_name)
    assert 'LoggingEnabled' in logging


def test_central_logs_bucket_logs_to_itself(s3_client, config):
    """Test that central logs bucket logs to itself."""
    bucket_name = config['name_for_central_logs_bucket']
    logging = s3_client.get_bucket_logging(Bucket=bucket_name)
    target_bucket = logging['LoggingEnabled']['TargetBucket']
    assert target_bucket == bucket_name


def test_central_logs_bucket_policy_has_firehose_statement(s3_client, config):
    """Test that central logs bucket policy has Firehose statement."""
    bucket_name = config['name_for_central_logs_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    assert 'AllowFirehoseWrite' in policy_doc


def test_central_logs_bucket_policy_firehose_allows_put_object(s3_client, config):
    """Test that Firehose is allowed to put objects to central logs."""
    bucket_name = config['name_for_central_logs_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    assert 's3:PutObject' in policy_doc


def test_central_logs_bucket_policy_firehose_restricts_to_cloudwatch_logs_prefix(
    s3_client, config
):
    """Test that Firehose is restricted to cloudwatch-logs prefix."""
    bucket_name = config['name_for_central_logs_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    assert 'cloudwatch-logs/*' in policy_doc


def test_central_logs_bucket_policy_firehose_requires_service_principal(s3_client, config):
    """Test that Firehose statement requires service principal."""
    bucket_name = config['name_for_central_logs_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    assert 'firehose.amazonaws.com' in policy_doc


def test_central_logs_bucket_force_destroy_in_tfstate(central_logs_bucket_attrs):
    """Test that central logs bucket has force_destroy enabled."""
    assert central_logs_bucket_attrs['force_destroy'] is True


def test_terraform_state_bucket_force_destroy_in_tfstate(terraform_state_bucket_attrs):
    """Test that terraform state bucket has force_destroy enabled."""
    assert terraform_state_bucket_attrs['force_destroy'] is True


# =============================================================================
# CloudTrail Configuration
# =============================================================================


def test_cloudtrail_trail_is_multi_region(cloudtrail_client):
    """Test that CloudTrail trail is multi-region."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert trail['IsMultiRegionTrail'] is True


def test_cloudtrail_includes_global_service_events(cloudtrail_client):
    """Test that CloudTrail includes global service events."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert trail['IncludeGlobalServiceEvents'] is True


def test_cloudtrail_has_log_file_validation_enabled(cloudtrail_client):
    """Test that CloudTrail has log file validation enabled."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert trail['LogFileValidationEnabled'] is True


def test_cloudtrail_is_actively_logging(cloudtrail_client):
    """Test that CloudTrail is actively logging."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    status = cloudtrail_client.get_trail_status(Name=trail['TrailARN'])
    assert status['IsLogging'] is True


def test_cloudtrail_s3_bucket_has_encryption(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket has encryption."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert 'ServerSideEncryptionConfiguration' in encryption


def test_cloudtrail_s3_bucket_blocks_public_acls(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket blocks public ACLs."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['BlockPublicAcls'] is True


def test_cloudtrail_s3_bucket_blocks_public_policy(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket blocks public policy."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['BlockPublicPolicy'] is True


def test_cloudtrail_s3_bucket_ignores_public_acls(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket ignores public ACLs."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['IgnorePublicAcls'] is True


def test_cloudtrail_s3_bucket_restricts_public_buckets(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket restricts public buckets."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['RestrictPublicBuckets'] is True


def test_cloudtrail_s3_bucket_versioning_disabled(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket versioning is disabled."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert versioning.get('Status') != 'Enabled'


def test_cloudtrail_has_cloudwatch_logs_configured(cloudtrail_client):
    """Test that CloudTrail has CloudWatch logs configured."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert 'CloudWatchLogsLogGroupArn' in trail


def test_cloudtrail_log_group_has_one_year_retention(logs_client, cloudtrail_log_group_name):
    """Test that CloudTrail log group has one year retention."""
    response = logs_client.describe_log_groups(logGroupNamePrefix=cloudtrail_log_group_name)
    log_group = response['logGroups'][0]
    assert log_group['retentionInDays'] == 365


def test_cloudtrail_captures_read_and_write_events(cloudtrail_client):
    """Test that CloudTrail captures both read and write events."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    selectors = cloudtrail_client.get_event_selectors(TrailName=trail['Name'])
    selector = selectors['EventSelectors'][0]
    assert selector['ReadWriteType'] == 'All'


def test_cloudtrail_includes_management_events(cloudtrail_client):
    """Test that CloudTrail includes management events."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    selectors = cloudtrail_client.get_event_selectors(TrailName=trail['Name'])
    selector = selectors['EventSelectors'][0]
    assert selector['IncludeManagementEvents'] is True


def test_access_log_bucket_has_encryption(s3_client, access_log_bucket):
    """Test that access log bucket has encryption enabled."""
    if access_log_bucket:
        encryption = s3_client.get_bucket_encryption(Bucket=access_log_bucket)
        assert 'ServerSideEncryptionConfiguration' in encryption


def test_access_log_bucket_versioning_disabled(s3_client, access_log_bucket):
    """Test that access log bucket versioning is disabled."""
    if access_log_bucket:
        versioning = s3_client.get_bucket_versioning(Bucket=access_log_bucket)
        assert versioning.get('Status') != 'Enabled'


def test_access_log_bucket_has_standard_ia_transition_at_30_days(s3_client, access_log_bucket):
    """Test that access log bucket has STANDARD_IA transition at 30 days."""
    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=access_log_bucket)
    rule = lifecycle['Rules'][0]
    transitions = rule['Transitions']
    standard_ia_transition = next(t for t in transitions if t['StorageClass'] == 'STANDARD_IA')
    assert standard_ia_transition['Days'] == 30


def test_access_log_bucket_has_glacier_transition_at_90_days(s3_client, access_log_bucket):
    """Test that access log bucket has GLACIER transition at 90 days."""
    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=access_log_bucket)
    rule = lifecycle['Rules'][0]
    glacier_transition = next(t for t in rule['Transitions'] if t['StorageClass'] == 'GLACIER')
    assert glacier_transition['Days'] == 90


def test_cloudtrail_bucket_enforces_ssl(s3_client, cloudtrail_client):
    """Test that CloudTrail bucket enforces SSL."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    assert 'aws:SecureTransport' in policy_doc or 'ssl' in policy_doc.lower()


# =============================================================================
# Route53 / DNS Configuration
# =============================================================================


def test_hosted_zone_is_public(route53_client, config):
    """Test that hosted zone is public."""
    domain_name = config['domain_name']
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = zones['HostedZones'][0]
    assert zone['Config']['PrivateZone'] is False


def test_google_verification_txt_record_has_correct_value(txt_record, config):
    """Test that Google verification TXT record has correct value."""
    google_verification = config['google_site_verification']
    expected_value = f'"google-site-verification={google_verification}"'
    record_values = [rr['Value'] for rr in txt_record['ResourceRecords']]
    assert expected_value in record_values


def test_google_verification_txt_record_has_ttl(txt_record):
    """Test that Google verification TXT record has TTL."""
    assert 'TTL' in txt_record


def test_gmail_mx_record_has_correct_priority(mx_record):
    """Test that Gmail MX record has correct priority."""
    record_values = [rr['Value'] for rr in mx_record['ResourceRecords']]
    assert any('1 smtp.google.com' in val for val in record_values)


def test_gmail_mx_record_has_ttl(mx_record):
    """Test that Gmail MX record has TTL."""
    assert 'TTL' in mx_record


def test_txt_record_ttl_equals_300(txt_record):
    """Test that TXT record TTL equals 300."""
    assert txt_record['TTL'] == 300


def test_mx_record_ttl_equals_300(mx_record):
    """Test that MX record TTL equals 300."""
    assert mx_record['TTL'] == 300


def test_mx_record_hostname_has_trailing_dot(mx_record):
    """Test that MX record hostname has trailing dot."""
    record_values = [rr['Value'] for rr in mx_record['ResourceRecords']]
    assert any('smtp.google.com.' in val for val in record_values)


def test_mx_record_priority_equals_one(mx_record):
    """Test that MX record priority equals one."""
    record_values = [rr['Value'] for rr in mx_record['ResourceRecords']]
    assert any(val.startswith('1 ') for val in record_values)


# =============================================================================
# IAM Configuration
# =============================================================================


def test_iam_role_trust_policy_has_federated_principal(iam_client, config):
    """Test that IAM role trust policy has federated principal."""
    role_name = config['name_for_github_actions_role']
    account_id = config['aws_account_id']
    oidc_provider = "token.actions.githubusercontent.com"
    expected_provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/{oidc_provider}"
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    federated_principal = trust_policy['Statement'][0]['Principal']['Federated']
    assert expected_provider_arn == federated_principal


def test_iam_role_trust_policy_has_correct_audience_condition(iam_client, config):
    """Test that IAM role trust policy has correct audience condition."""
    role_name = config['name_for_github_actions_role']
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    condition = trust_policy['Statement'][0]['Condition']
    string_equals = condition['StringEquals']
    aud_value = string_equals['token.actions.githubusercontent.com:aud']
    assert aud_value == 'sts.amazonaws.com'


def test_iam_role_trust_policy_has_correct_subject_condition(iam_client, config):
    """Test that IAM role trust policy has correct subject condition."""
    role_name = config['name_for_github_actions_role']
    github_org = config['github_org']
    github_repo = config['name_for_github_repo']
    expected_pattern = f"repo:{github_org}/{github_repo}:*"
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    condition = trust_policy['Statement'][0]['Condition']
    string_like = condition['StringLike']
    sub_value = string_like['token.actions.githubusercontent.com:sub']
    assert sub_value == expected_pattern


def test_iam_role_has_administrator_access_policy(iam_client, config):
    """Test that IAM role has AdministratorAccess policy."""
    role_name = config['name_for_github_actions_role']
    response = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arn = response['AttachedPolicies'][0]['PolicyArn']
    assert policy_arn == 'arn:aws:iam::aws:policy/AdministratorAccess'


def test_github_actions_role_name_is_pascalcase(iam_client, config):
    """Verify GitHub Actions IAM role name uses PascalCase."""
    role_name = config.get('name_for_github_actions_role', 'TenULabsGitHubActionsRole')
    assert_iam_role_name_is_pascalcase(iam_client, role_name, validate_name)
    assert True  # Explicit pass


def test_cloudtrail_iam_role_name_is_pascalcase(config):
    """Verify CloudTrail IAM role name uses PascalCase."""
    role_name = config.get('name_for_cloudtrail_iam_role')
    error = validate_name(role_name)
    assert error is None, f"CloudTrail IAM role name '{role_name}' is not PascalCase: {error}"


# =============================================================================
# OIDC Configuration
# =============================================================================


def test_oidc_provider_has_correct_thumbprint(iam_client, config):
    """Test that OIDC provider has correct thumbprint."""
    account_id = config['aws_account_id']
    provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
    thumbprint = response['ThumbprintList'][0]
    assert thumbprint == '6938fd4d98bab03faadb97b34396831e3780aea1'


def test_oidc_provider_has_correct_client_id(iam_client, config):
    """Test that OIDC provider has correct client ID."""
    account_id = config['aws_account_id']
    provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
    client_id = response['ClientIDList'][0]
    assert client_id == 'sts.amazonaws.com'


# =============================================================================
# SSM Configuration
# =============================================================================


def test_github_pat_parameter_type_is_secure_string(ssm_client, config):
    """Test that GitHub PAT parameter is SecureString type."""
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [config['ssm_parameter_name_for_github_pat']]}]
    )
    parameter = response['Parameters'][0]
    assert parameter['Type'] == 'SecureString'


def test_github_pat_parameter_has_value(ssm_client, config):
    """Test that GitHub PAT parameter has a value."""
    param_name = config['ssm_parameter_name_for_github_pat']
    response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
    parameter_value = response['Parameter']['Value']
    assert parameter_value != ''


def test_github_pat_parameter_value_is_not_placeholder(ssm_client, config):
    """Test that GitHub PAT parameter value is not a placeholder."""
    param_name = config['ssm_parameter_name_for_github_pat']
    response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
    parameter_value = response['Parameter']['Value']
    assert not parameter_value.startswith('PLACEHOLDER')


def test_github_app_id_parameter_type_is_string(ssm_client, config):
    """Test that GitHub App ID parameter type is String."""
    param_name = f"{config['github_app_ssm_prefix']}/id"
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [param_name]}]
    )
    assert response['Parameters'][0]['Type'] == 'String'


def test_github_app_installation_id_parameter_type_is_string(ssm_client, config):
    """Test that GitHub App installation ID parameter type is String."""
    param_name = f"{config['github_app_ssm_prefix']}/installation_id"
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [param_name]}]
    )
    assert response['Parameters'][0]['Type'] == 'String'


def test_github_app_private_key_parameter_type_is_secure_string(ssm_client, config):
    """Test that GitHub App private key parameter type is SecureString."""
    param_name = f"{config['github_app_ssm_prefix']}/private_key"
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [param_name]}]
    )
    assert response['Parameters'][0]['Type'] == 'SecureString'


def test_github_app_private_key_parameter_has_value(ssm_client, config):
    """Test that GitHub App private key parameter has a value."""
    param_name = f"{config['github_app_ssm_prefix']}/private_key"
    response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
    assert response['Parameter']['Value'] != ''


# =============================================================================
# Terraform State Bucket Configuration
# =============================================================================


def test_terraform_state_bucket_has_encryption(s3_client, config):
    """Test that terraform state bucket has encryption enabled."""
    bucket_name = config['name_for_terraform_state_bucket']
    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert 'ServerSideEncryptionConfiguration' in encryption


def test_terraform_state_bucket_encryption_is_aes256(s3_client, config):
    """Test that terraform state bucket uses AES256 encryption."""
    bucket_name = config['name_for_terraform_state_bucket']
    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    rules = encryption['ServerSideEncryptionConfiguration']['Rules']
    algorithm = rules[0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
    assert algorithm == 'AES256'


def test_terraform_state_bucket_blocks_public_acls(s3_client, config):
    """Test that terraform state bucket blocks public ACLs."""
    bucket_name = config['name_for_terraform_state_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['BlockPublicAcls'] is True


def test_terraform_state_bucket_blocks_public_policy(s3_client, config):
    """Test that terraform state bucket blocks public policy."""
    bucket_name = config['name_for_terraform_state_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['BlockPublicPolicy'] is True


def test_terraform_state_bucket_ignores_public_acls(s3_client, config):
    """Test that terraform state bucket ignores public ACLs."""
    bucket_name = config['name_for_terraform_state_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['IgnorePublicAcls'] is True


def test_terraform_state_bucket_restricts_public_buckets(s3_client, config):
    """Test that terraform state bucket restricts public buckets."""
    bucket_name = config['name_for_terraform_state_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['RestrictPublicBuckets'] is True


def test_terraform_state_bucket_has_policy(s3_client, config):
    """Test that terraform state bucket has a bucket policy."""
    bucket_name = config['name_for_terraform_state_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    assert 'Policy' in policy


def test_terraform_state_bucket_policy_denies_insecure_transport(s3_client, config):
    """Test that terraform state bucket policy denies insecure transport."""
    bucket_name = config['name_for_terraform_state_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    assert 'aws:SecureTransport' in policy_doc


def test_terraform_state_bucket_has_logging_enabled(s3_client, config):
    """Test that terraform state bucket has logging enabled."""
    bucket_name = config['name_for_terraform_state_bucket']
    logging = s3_client.get_bucket_logging(Bucket=bucket_name)
    assert 'LoggingEnabled' in logging


def test_terraform_state_bucket_logs_to_central_logs(s3_client, config):
    """Test that terraform state bucket logs to central logs bucket."""
    bucket_name = config['name_for_terraform_state_bucket']
    logging = s3_client.get_bucket_logging(Bucket=bucket_name)
    target_bucket = logging['LoggingEnabled']['TargetBucket']
    assert target_bucket == config['name_for_central_logs_bucket']
