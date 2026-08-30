import json
import pytest

from test_fixtures.aws import find_lifecycle_rule, stale_delete_markers


def find_tfstate_resource(state, resource_type, resource_name):
    for resource in state['resources']:
        if resource['type'] == resource_type and resource['name'] == resource_name:
            return resource['instances'][0]['attributes']
    return None


@pytest.fixture(name='tfstate')
def tfstate_fixture(s3_client, config):
    response = s3_client.get_object(
        Bucket=config['name_for_terraform_state_bucket'],
        Key='bootstrap/terraform.tfstate'
    )
    return json.loads(response['Body'].read().decode('utf-8'))


@pytest.fixture(name='terraform_state_bucket_attrs')
def terraform_state_bucket_attrs_fixture(tfstate):
    return find_tfstate_resource(tfstate, 'aws_s3_bucket', 'terraform_state')


@pytest.fixture(name='central_logs_bucket_attrs')
def central_logs_bucket_attrs_fixture(tfstate):
    return find_tfstate_resource(tfstate, 'aws_s3_bucket', 'central_logs')


def test_central_logs_bucket_has_encryption(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert 'ServerSideEncryptionConfiguration' in encryption


def test_central_logs_bucket_encryption_is_aes256(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    rules = encryption['ServerSideEncryptionConfiguration']['Rules']
    algorithm = rules[0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
    assert algorithm == 'AES256'


def test_central_logs_bucket_blocks_public_acls(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['BlockPublicAcls'] is True


def test_central_logs_bucket_blocks_public_policy(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['BlockPublicPolicy'] is True


def test_central_logs_bucket_ignores_public_acls(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['IgnorePublicAcls'] is True


def test_central_logs_bucket_restricts_public_buckets(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['RestrictPublicBuckets'] is True


def test_central_logs_bucket_versioning_disabled(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert versioning.get('Status') != 'Enabled'


def test_central_logs_bucket_has_log_delivery_write_acl(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    acl = s3_client.get_bucket_acl(Bucket=bucket_name)
    grantees = [g['Grantee'].get('URI', '') for g in acl.get('Grants', [])]
    log_delivery_uri = 'http://acs.amazonaws.com/groups/s3/LogDelivery'
    assert any(log_delivery_uri in g for g in grantees)


def test_central_logs_bucket_ownership_is_bucket_owner_preferred(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    ownership = s3_client.get_bucket_ownership_controls(Bucket=bucket_name)
    rules = ownership['OwnershipControls']['Rules']
    assert rules[0]['ObjectOwnership'] == 'BucketOwnerPreferred'


def test_central_logs_bucket_has_lifecycle_configuration(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    assert 'Rules' in lifecycle


def test_central_logs_bucket_has_standard_ia_transition(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    rule = lifecycle['Rules'][0]
    storage_classes = [t['StorageClass'] for t in rule['Transitions']]
    assert 'STANDARD_IA' in storage_classes


def test_central_logs_bucket_has_glacier_transition(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    rule = lifecycle['Rules'][0]
    storage_classes = [t['StorageClass'] for t in rule['Transitions']]
    assert 'GLACIER' in storage_classes


def test_central_logs_bucket_has_expiration(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    rule = lifecycle['Rules'][0]
    assert 'Expiration' in rule


def test_central_logs_bucket_has_policy(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    assert 'Policy' in policy


def test_central_logs_bucket_policy_denies_insecure_transport(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    assert 'aws:SecureTransport' in policy_doc


def test_central_logs_bucket_has_logging_enabled(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    logging = s3_client.get_bucket_logging(Bucket=bucket_name)
    assert 'LoggingEnabled' in logging


def test_central_logs_bucket_logs_to_itself(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    logging = s3_client.get_bucket_logging(Bucket=bucket_name)
    target_bucket = logging['LoggingEnabled']['TargetBucket']
    assert target_bucket == bucket_name


def test_central_logs_bucket_policy_has_firehose_statement(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    assert 'AllowFirehoseWrite' in policy_doc


def test_central_logs_bucket_policy_firehose_allows_put_object(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    assert 's3:PutObject' in policy_doc


def test_central_logs_bucket_policy_firehose_restricts_to_cloudwatch_logs_prefix(
    s3_client, config
):
    bucket_name = config['name_for_central_logs_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    assert 'cloudwatch-logs/*' in policy_doc


def test_central_logs_bucket_policy_firehose_requires_service_principal(s3_client, config):
    bucket_name = config['name_for_central_logs_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    assert 'firehose.amazonaws.com' in policy_doc


def test_central_logs_bucket_force_destroy_in_tfstate(central_logs_bucket_attrs):
    assert central_logs_bucket_attrs['force_destroy'] is True


def test_terraform_state_bucket_force_destroy_in_tfstate(terraform_state_bucket_attrs):
    assert terraform_state_bucket_attrs['force_destroy'] is True


def test_terraform_state_bucket_expires_delete_markers(s3_client, config):
    bucket_name = config['name_for_terraform_state_bucket']
    rule = find_lifecycle_rule(s3_client, bucket_name, 'expire-delete-markers') or {}
    assert rule.get('Expiration', {}).get('ExpiredObjectDeleteMarker') is True


def test_terraform_state_bucket_keeps_no_stale_delete_markers(s3_client, config):
    bucket_name = config['name_for_terraform_state_bucket']
    markers = stale_delete_markers(s3_client, bucket_name)
    assert not markers, f"delete markers nothing will remove: {markers}"


def test_cloudtrail_trail_is_multi_region(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert trail['IsMultiRegionTrail'] is True


def test_cloudtrail_includes_global_service_events(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert trail['IncludeGlobalServiceEvents'] is True


def test_cloudtrail_has_log_file_validation_enabled(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert trail['LogFileValidationEnabled'] is True


def test_cloudtrail_is_actively_logging(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    status = cloudtrail_client.get_trail_status(Name=trail['TrailARN'])
    assert status['IsLogging'] is True


def test_cloudtrail_s3_bucket_has_encryption(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert 'ServerSideEncryptionConfiguration' in encryption


def test_cloudtrail_s3_bucket_blocks_public_acls(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['BlockPublicAcls'] is True


def test_cloudtrail_s3_bucket_blocks_public_policy(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['BlockPublicPolicy'] is True


def test_cloudtrail_s3_bucket_ignores_public_acls(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['IgnorePublicAcls'] is True


def test_cloudtrail_s3_bucket_restricts_public_buckets(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['RestrictPublicBuckets'] is True


def test_cloudtrail_s3_bucket_versioning_disabled(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert versioning.get('Status') != 'Enabled'


def test_cloudtrail_has_cloudwatch_logs_configured(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert 'CloudWatchLogsLogGroupArn' in trail


def test_cloudtrail_log_group_has_one_year_retention(logs_client, cloudtrail_log_group_name):
    response = logs_client.describe_log_groups(logGroupNamePrefix=cloudtrail_log_group_name)
    log_group = response['logGroups'][0]
    assert log_group['retentionInDays'] == 365


def test_cloudtrail_captures_read_and_write_events(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    selectors = cloudtrail_client.get_event_selectors(TrailName=trail['Name'])
    selector = selectors['EventSelectors'][0]
    assert selector['ReadWriteType'] == 'All'


def test_cloudtrail_includes_management_events(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    selectors = cloudtrail_client.get_event_selectors(TrailName=trail['Name'])
    selector = selectors['EventSelectors'][0]
    assert selector['IncludeManagementEvents'] is True


def test_access_log_bucket_has_encryption(s3_client, access_log_bucket):
    if access_log_bucket:
        encryption = s3_client.get_bucket_encryption(Bucket=access_log_bucket)
        assert 'ServerSideEncryptionConfiguration' in encryption


def test_access_log_bucket_versioning_disabled(s3_client, access_log_bucket):
    if access_log_bucket:
        versioning = s3_client.get_bucket_versioning(Bucket=access_log_bucket)
        assert versioning.get('Status') != 'Enabled'


def test_access_log_bucket_has_standard_ia_transition_at_30_days(s3_client, access_log_bucket):
    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=access_log_bucket)
    rule = lifecycle['Rules'][0]
    transitions = rule['Transitions']
    standard_ia_transition = next(t for t in transitions if t['StorageClass'] == 'STANDARD_IA')
    assert standard_ia_transition['Days'] == 30


def test_access_log_bucket_has_glacier_transition_at_90_days(s3_client, access_log_bucket):
    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=access_log_bucket)
    rule = lifecycle['Rules'][0]
    glacier_transition = next(t for t in rule['Transitions'] if t['StorageClass'] == 'GLACIER')
    assert glacier_transition['Days'] == 90


def test_cloudtrail_bucket_enforces_ssl(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    assert 'aws:SecureTransport' in policy_doc or 'ssl' in policy_doc.lower()


def test_hosted_zone_is_public(route53_client, config):
    domain_name = config['domain_name']
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = zones['HostedZones'][0]
    assert zone['Config']['PrivateZone'] is False


def test_google_verification_txt_record_has_correct_value(txt_record, config):
    google_verification = config['google_site_verification']
    expected_value = f'"google-site-verification={google_verification}"'
    record_values = [rr['Value'] for rr in txt_record['ResourceRecords']]
    assert expected_value in record_values


def test_google_verification_txt_record_has_ttl(txt_record):
    assert 'TTL' in txt_record


def test_gmail_mx_record_has_correct_priority(mx_record):
    record_values = [rr['Value'] for rr in mx_record['ResourceRecords']]
    assert any('1 smtp.google.com' in val for val in record_values)


def test_gmail_mx_record_has_ttl(mx_record):
    assert 'TTL' in mx_record


def test_txt_record_ttl_equals_300(txt_record):
    assert txt_record['TTL'] == 300


def test_mx_record_ttl_equals_300(mx_record):
    assert mx_record['TTL'] == 300


def test_mx_record_hostname_has_trailing_dot(mx_record):
    record_values = [rr['Value'] for rr in mx_record['ResourceRecords']]
    assert any('smtp.google.com.' in val for val in record_values)


def test_mx_record_priority_equals_one(mx_record):
    record_values = [rr['Value'] for rr in mx_record['ResourceRecords']]
    assert any(val.startswith('1 ') for val in record_values)


def test_iam_role_trust_policy_has_federated_principal(iam_client, config, aws_account_id):
    role_name = config['name_for_github_actions_role']
    account_id = aws_account_id
    oidc_provider = "token.actions.githubusercontent.com"
    expected_provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/{oidc_provider}"
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    federated_principal = trust_policy['Statement'][0]['Principal']['Federated']
    assert expected_provider_arn == federated_principal


def test_iam_role_trust_policy_has_correct_audience_condition(iam_client, config):
    role_name = config['name_for_github_actions_role']
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    condition = trust_policy['Statement'][0]['Condition']
    string_equals = condition['StringEquals']
    aud_value = string_equals['token.actions.githubusercontent.com:aud']
    assert aud_value == 'sts.amazonaws.com'


def test_iam_role_trust_policy_has_correct_subject_condition(iam_client, config):
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
    role_name = config['name_for_github_actions_role']
    response = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arn = response['AttachedPolicies'][0]['PolicyArn']
    assert policy_arn == 'arn:aws:iam::aws:policy/AdministratorAccess'


def _trusted_repository_patterns(trust_policy):
    condition = trust_policy['Statement'][0]['Condition']['StringLike']
    subjects = condition['token.actions.githubusercontent.com:sub']
    return [subjects] if isinstance(subjects, str) else subjects


@pytest.mark.parametrize("suffix", ["WanSynthesizerRole"])
def test_deploy_role_trusts_only_the_synthesizer(iam_client, config, suffix):
    role_name = f"{config['resource_prefix']}{suffix}"
    org = config['github_org']
    expected = [
        f"repo:{org}/wan-synthesizer:*",
        f"repo:{org}@240548037/wan-synthesizer@1262350676:*",
    ]
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    assert sorted(_trusted_repository_patterns(trust_policy)) == sorted(expected)


def test_oidc_provider_has_correct_thumbprint(iam_client, aws_account_id):
    account_id = aws_account_id
    provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
    thumbprint = response['ThumbprintList'][0]
    assert thumbprint == '6938fd4d98bab03faadb97b34396831e3780aea1'


def test_oidc_provider_has_correct_client_id(iam_client, aws_account_id):
    account_id = aws_account_id
    provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
    client_id = response['ClientIDList'][0]
    assert client_id == 'sts.amazonaws.com'


def test_github_pat_parameter_type_is_secure_string(ssm_client, config):
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [config['ssm_parameter_name_for_github_pat']]}]
    )
    parameter = response['Parameters'][0]
    assert parameter['Type'] == 'SecureString'


def test_github_pat_parameter_has_value(ssm_client, config):
    param_name = config['ssm_parameter_name_for_github_pat']
    response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
    parameter_value = response['Parameter']['Value']
    assert parameter_value != ''


def test_github_pat_parameter_value_is_not_placeholder(ssm_client, config):
    param_name = config['ssm_parameter_name_for_github_pat']
    response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
    parameter_value = response['Parameter']['Value']
    assert not parameter_value.startswith('PLACEHOLDER')


def test_github_app_id_parameter_type_is_string(ssm_client, config):
    param_name = f"{config['github_app_ssm_prefix']}/id"
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [param_name]}]
    )
    assert response['Parameters'][0]['Type'] == 'String'


def test_github_app_installation_id_parameter_type_is_string(ssm_client, config):
    param_name = f"{config['github_app_ssm_prefix']}/installation_id"
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [param_name]}]
    )
    assert response['Parameters'][0]['Type'] == 'String'


def test_github_app_private_key_parameter_type_is_secure_string(ssm_client, config):
    param_name = f"{config['github_app_ssm_prefix']}/private_key"
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [param_name]}]
    )
    assert response['Parameters'][0]['Type'] == 'SecureString'


def test_github_app_private_key_parameter_has_value(ssm_client, config):
    param_name = f"{config['github_app_ssm_prefix']}/private_key"
    response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
    assert response['Parameter']['Value'] != ''


def test_terraform_state_bucket_versioning_is_suspended(s3_client, config):
    bucket_name = config['name_for_terraform_state_bucket']
    versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert versioning.get('Status') == 'Suspended'


def test_terraform_state_bucket_has_encryption(s3_client, config):
    bucket_name = config['name_for_terraform_state_bucket']
    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert 'ServerSideEncryptionConfiguration' in encryption


def test_terraform_state_bucket_encryption_is_aes256(s3_client, config):
    bucket_name = config['name_for_terraform_state_bucket']
    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
    rules = encryption['ServerSideEncryptionConfiguration']['Rules']
    algorithm = rules[0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
    assert algorithm == 'AES256'


def test_terraform_state_bucket_blocks_public_acls(s3_client, config):
    bucket_name = config['name_for_terraform_state_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['BlockPublicAcls'] is True


def test_terraform_state_bucket_blocks_public_policy(s3_client, config):
    bucket_name = config['name_for_terraform_state_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['BlockPublicPolicy'] is True


def test_terraform_state_bucket_ignores_public_acls(s3_client, config):
    bucket_name = config['name_for_terraform_state_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['IgnorePublicAcls'] is True


def test_terraform_state_bucket_restricts_public_buckets(s3_client, config):
    bucket_name = config['name_for_terraform_state_bucket']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    block_config = public_access['PublicAccessBlockConfiguration']
    assert block_config['RestrictPublicBuckets'] is True


def test_terraform_state_bucket_has_policy(s3_client, config):
    bucket_name = config['name_for_terraform_state_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    assert 'Policy' in policy


def test_terraform_state_bucket_policy_denies_insecure_transport(s3_client, config):
    bucket_name = config['name_for_terraform_state_bucket']
    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
    policy_doc = policy['Policy']
    assert 'aws:SecureTransport' in policy_doc


def test_terraform_state_bucket_has_logging_enabled(s3_client, config):
    bucket_name = config['name_for_terraform_state_bucket']
    logging = s3_client.get_bucket_logging(Bucket=bucket_name)
    assert 'LoggingEnabled' in logging


def test_terraform_state_bucket_logs_to_central_logs(s3_client, config):
    bucket_name = config['name_for_terraform_state_bucket']
    logging = s3_client.get_bucket_logging(Bucket=bucket_name)
    target_bucket = logging['LoggingEnabled']['TargetBucket']
    assert target_bucket == config['name_for_central_logs_bucket']
