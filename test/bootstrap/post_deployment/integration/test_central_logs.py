"""Integration tests for central logs bucket configuration."""


def test_central_logs_bucket_exists(s3_client, config):
    """Test that central logs bucket exists."""
    bucket_name = config['name_for_central_logs_bucket']
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


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


def test_central_logs_write_policy_exists(iam_client):
    """Test that central logs write policy exists."""
    policy_name = 'central-logs-write-policy'
    response = iam_client.list_policies(Scope='Local')
    policy_names = [p['PolicyName'] for p in response['Policies']]
    assert policy_name in policy_names


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
