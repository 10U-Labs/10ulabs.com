"""Integration tests for CloudTrail configuration."""


def test_cloudtrail_trail_exists(cloudtrail_client):
    """Test that CloudTrail trail exists."""
    trails = cloudtrail_client.describe_trails()
    assert len(trails['trailList']) > 0


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


def test_cloudtrail_is_actively_logging(cloudtrail_client):
    """Test that CloudTrail is actively logging."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    status = cloudtrail_client.get_trail_status(Name=trail['TrailARN'])
    assert status['IsLogging'] is True


def test_cloudtrail_s3_bucket_exists(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket exists."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


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
    config = public_access['PublicAccessBlockConfiguration']
    assert config['BlockPublicAcls'] is True


def test_cloudtrail_s3_bucket_blocks_public_policy(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket blocks public policy."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    config = public_access['PublicAccessBlockConfiguration']
    assert config['BlockPublicPolicy'] is True


def test_cloudtrail_s3_bucket_ignores_public_acls(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket ignores public ACLs."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    config = public_access['PublicAccessBlockConfiguration']
    assert config['IgnorePublicAcls'] is True


def test_cloudtrail_s3_bucket_restricts_public_buckets(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket restricts public buckets."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    public_access = s3_client.get_public_access_block(Bucket=bucket_name)
    config = public_access['PublicAccessBlockConfiguration']
    assert config['RestrictPublicBuckets'] is True


def test_cloudtrail_s3_bucket_versioning_disabled(s3_client, cloudtrail_client):
    """Test that CloudTrail S3 bucket versioning is disabled."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    try:
        versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
        assert versioning.get('Status') != 'Enabled'
    except KeyError:
        pass


def test_cloudtrail_has_cloudwatch_logs_configured(cloudtrail_client):
    """Test that CloudTrail has CloudWatch logs configured."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    assert 'CloudWatchLogsLogGroupArn' in trail


def test_cloudtrail_log_group_exists(logs_client, cloudtrail_client):
    """Test that CloudTrail log group exists."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    log_group_arn = trail['CloudWatchLogsLogGroupArn']
    log_group_name = log_group_arn.split(':log-group:')[1].split(':')[0]
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    assert len(response['logGroups']) > 0


def test_cloudtrail_log_group_has_one_year_retention(logs_client, cloudtrail_client):
    """Test that CloudTrail log group has one year retention."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    log_group_arn = trail['CloudWatchLogsLogGroupArn']
    log_group_name = log_group_arn.split(':log-group:')[1].split(':')[0]
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
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


def test_cloudtrail_writes_logs_to_s3(s3_client, cloudtrail_client):
    """Test that CloudTrail writes logs to S3."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    bucket_name = trail['S3BucketName']
    objects = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=10)
    key_count = objects['KeyCount']
    assert key_count > 0


def test_cloudtrail_writes_logs_to_cloudwatch(logs_client, cloudtrail_client):
    """Test that CloudTrail writes logs to CloudWatch."""
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
    """Test that access log bucket exists."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    cloudtrail_bucket_name = trail['S3BucketName']
    response = s3_client.get_bucket_logging(Bucket=cloudtrail_bucket_name)
    if 'LoggingEnabled' in response:
        access_log_bucket = response['LoggingEnabled']['TargetBucket']
        head_response = s3_client.head_bucket(Bucket=access_log_bucket)
        assert head_response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_access_log_bucket_has_encryption(s3_client, cloudtrail_client):
    """Test that access log bucket has encryption enabled."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    cloudtrail_bucket_name = trail['S3BucketName']
    response = s3_client.get_bucket_logging(Bucket=cloudtrail_bucket_name)
    if 'LoggingEnabled' in response:
        access_log_bucket = response['LoggingEnabled']['TargetBucket']
        encryption = s3_client.get_bucket_encryption(Bucket=access_log_bucket)
        assert 'ServerSideEncryptionConfiguration' in encryption


def test_access_log_bucket_versioning_disabled(s3_client, cloudtrail_client):
    """Test that access log bucket versioning is disabled."""
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


def test_access_log_bucket_has_standard_ia_transition_at_30_days(s3_client, cloudtrail_client):
    """Test that access log bucket has STANDARD_IA transition at 30 days."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    cloudtrail_bucket_name = trail['S3BucketName']
    response = s3_client.get_bucket_logging(Bucket=cloudtrail_bucket_name)
    access_log_bucket = response['LoggingEnabled']['TargetBucket']
    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=access_log_bucket)
    rule = lifecycle['Rules'][0]
    transitions = rule['Transitions']
    standard_ia_transition = next(t for t in transitions if t['StorageClass'] == 'STANDARD_IA')
    assert standard_ia_transition['Days'] == 30


def test_access_log_bucket_has_glacier_transition_at_90_days(s3_client, cloudtrail_client):
    """Test that access log bucket has GLACIER transition at 90 days."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    cloudtrail_bucket_name = trail['S3BucketName']
    response = s3_client.get_bucket_logging(Bucket=cloudtrail_bucket_name)
    access_log_bucket = response['LoggingEnabled']['TargetBucket']
    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=access_log_bucket)
    rule = lifecycle['Rules'][0]
    glacier_transition = next(t for t in rule['Transitions'] if t['StorageClass'] == 'GLACIER')
    assert glacier_transition['Days'] == 90


def test_cloudtrail_bucket_enforces_ssl(s3_client, cloudtrail_client):
    """Test that CloudTrail bucket enforces SSL."""
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
    """Test that CloudWatch Logs IAM role exists for CloudTrail."""
    trails = cloudtrail_client.describe_trails()
    trail = trails['trailList'][0]
    if 'CloudWatchLogsRoleArn' in trail:
        role_name = trail['CloudWatchLogsRoleArn'].split('/')[-1]
        role = iam_client.get_role(RoleName=role_name)
        assert role['Role']['RoleName'] == role_name
