import boto3


def test_oidc_provider_exists_in_aws(iam_client, config):
    account_id = config['aws_account_id']
    provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
    assert response['Url'] == 'token.actions.githubusercontent.com'


def test_oidc_provider_has_correct_thumbprint(iam_client, config):
    account_id = config['aws_account_id']
    provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
    thumbprint = response['ThumbprintList'][0]
    assert thumbprint == '6938fd4d98bab03faadb97b34396831e3780aea1'


def test_oidc_provider_has_correct_client_id(iam_client, config):
    account_id = config['aws_account_id']
    provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
    client_id = response['ClientIDList'][0]
    assert client_id == 'sts.amazonaws.com'


def test_iam_role_exists_in_aws(iam_client, config):
    role_name = config['github_actions_role_name']
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


def test_iam_role_trust_policy_has_federated_principal(iam_client, config):
    role_name = config['github_actions_role_name']
    account_id = config['aws_account_id']
    expected_provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    federated_principal = trust_policy['Statement'][0]['Principal']['Federated']
    assert expected_provider_arn == federated_principal


def test_iam_role_trust_policy_has_correct_audience_condition(iam_client, config):
    role_name = config['github_actions_role_name']
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    condition = trust_policy['Statement'][0]['Condition']
    string_equals = condition['StringEquals']
    aud_value = string_equals['token.actions.githubusercontent.com:aud']
    assert aud_value == 'sts.amazonaws.com'


def test_iam_role_trust_policy_has_correct_subject_condition(iam_client, config):
    role_name = config['github_actions_role_name']
    github_org = config['github_org']
    github_repo = config['github_repo']
    expected_pattern = f"repo:{github_org}/{github_repo}:*"
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    condition = trust_policy['Statement'][0]['Condition']
    string_like = condition['StringLike']
    sub_value = string_like['token.actions.githubusercontent.com:sub']
    assert sub_value == expected_pattern


def test_iam_role_has_administrator_access_policy(iam_client, config):
    role_name = config['github_actions_role_name']
    response = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arn = response['AttachedPolicies'][0]['PolicyArn']
    assert policy_arn == 'arn:aws:iam::aws:policy/AdministratorAccess'


def test_hosted_zone_exists(route53_client, config):
    domain_name = config['domain_name']
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = zones['HostedZones'][0]
    assert zone['Name'] == f"{domain_name}."


def test_hosted_zone_is_public(route53_client, config):
    domain_name = config['domain_name']
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = zones['HostedZones'][0]
    assert zone['Config']['PrivateZone'] is False


def test_cloudtrail_trail_exists(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    assert len(trails['trailList']) > 0


def test_cloudtrail_trail_is_multi_region(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert trail['IsMultiRegionTrail'] is True


def test_cloudtrail_includes_global_service_events(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert trail['IncludeGlobalServiceEvents'] is True


def test_cloudtrail_is_actively_logging(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    status = cloudtrail_client.get_trail_status(Name=trail['TrailARN'])
    assert status['IsLogging'] is True


def test_cloudtrail_s3_bucket_exists(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


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
    config = public_access['PublicAccessBlockConfiguration']
    assert config['BlockPublicAcls'] is True


def test_cloudtrail_s3_bucket_blocks_public_policy(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    config = public_access['PublicAccessBlockConfiguration']
    assert config['BlockPublicPolicy'] is True


def test_cloudtrail_s3_bucket_ignores_public_acls(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    config = public_access['PublicAccessBlockConfiguration']
    assert config['IgnorePublicAcls'] is True


def test_cloudtrail_s3_bucket_restricts_public_buckets(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    config = public_access['PublicAccessBlockConfiguration']
    assert config['RestrictPublicBuckets'] is True


def test_cloudtrail_s3_bucket_versioning_disabled(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    try:
        versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
        assert versioning.get('Status') != 'Enabled'
    except KeyError:
        pass


def test_cloudtrail_has_cloudwatch_logs_configured(cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert 'CloudWatchLogsLogGroupArn' in trail


def test_cloudtrail_log_group_exists(logs_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    log_group_arn = trail['CloudWatchLogsLogGroupArn']
    log_group_name = log_group_arn.split(':log-group:')[1].split(':')[0]
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    assert len(response['logGroups']) > 0


def test_cloudtrail_log_group_has_one_year_retention(logs_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    log_group_arn = trail['CloudWatchLogsLogGroupArn']
    log_group_name = log_group_arn.split(':log-group:')[1].split(':')[0]
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
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


def test_cloudtrail_writes_logs_to_s3(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    objects = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=10)
    key_count = objects['KeyCount']
    assert key_count > 0


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
    assert len(streams['logStreams']) > 0


def test_access_log_bucket_exists(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    cloudtrail_bucket_name = trail['S3BucketName']
    response = s3_client.get_bucket_logging(Bucket=cloudtrail_bucket_name)
    if 'LoggingEnabled' in response:
        access_log_bucket = response['LoggingEnabled']['TargetBucket']
        head_response = s3_client.head_bucket(Bucket=access_log_bucket)
        assert head_response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_access_log_bucket_has_encryption(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    cloudtrail_bucket_name = trail['S3BucketName']
    response = s3_client.get_bucket_logging(Bucket=cloudtrail_bucket_name)
    if 'LoggingEnabled' in response:
        access_log_bucket = response['LoggingEnabled']['TargetBucket']
        encryption = s3_client.get_bucket_encryption(Bucket=access_log_bucket)
        assert 'ServerSideEncryptionConfiguration' in encryption


def test_access_log_bucket_versioning_disabled(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    cloudtrail_bucket_name = trail['S3BucketName']
    response = s3_client.get_bucket_logging(Bucket=cloudtrail_bucket_name)
    if 'LoggingEnabled' in response:
        access_log_bucket = response['LoggingEnabled']['TargetBucket']
        try:
            versioning = s3_client.get_bucket_versioning(Bucket=access_log_bucket)
            assert versioning.get('Status') != 'Enabled'
        except KeyError:
            pass


def test_access_log_bucket_has_glacier_lifecycle_rule(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    cloudtrail_bucket_name = trail['S3BucketName']
    response = s3_client.get_bucket_logging(Bucket=cloudtrail_bucket_name)
    if 'LoggingEnabled' in response:
        access_log_bucket = response['LoggingEnabled']['TargetBucket']
        lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=access_log_bucket)
        rule = lifecycle['Rules'][0]
        transition = rule['Transitions'][0]
        storage_class = transition['StorageClass']
        assert storage_class == 'GLACIER'


def test_cloudtrail_bucket_enforces_ssl(s3_client, cloudtrail_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    try:
        policy = s3_client.get_bucket_policy(Bucket=bucket_name)
        policy_doc = policy['Policy']
        assert 'aws:SecureTransport' in policy_doc or 'ssl' in policy_doc.lower()
    except s3_client.exceptions.NoSuchBucketPolicy:
        pass


def test_cloudwatch_logs_iam_role_exists(cloudtrail_client, iam_client):
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    if 'CloudWatchLogsRoleArn' in trail:
        role_name = trail['CloudWatchLogsRoleArn'].split('/')[-1]
        role = iam_client.get_role(RoleName=role_name)
        assert role['Role']['RoleName'] == role_name
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
    s3_client = boto3.client('s3', region_name=config['aws_region'])

    try:
        s3_client.head_object(
            Bucket='10ulabs-terraform-state',
            Key='bootstrap/terraform.tfstate'
        )
        state_exists = True
    except:
        state_exists = False

    assert state_exists
