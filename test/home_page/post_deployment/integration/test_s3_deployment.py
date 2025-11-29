def test_s3_bucket_exists(s3_client, config):
    response = s3_client.head_bucket(Bucket=config['website_fqdn'])
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_s3_bucket_has_public_access_blocked(s3_client, config):
    response = s3_client.get_public_access_block(Bucket=config['website_fqdn'])
    config_block = response['PublicAccessBlockConfiguration']
    assert config_block['BlockPublicAcls'] is True


def test_s3_bucket_has_block_public_policy(s3_client, config):
    response = s3_client.get_public_access_block(Bucket=config['website_fqdn'])
    config_block = response['PublicAccessBlockConfiguration']
    assert config_block['BlockPublicPolicy'] is True


def test_s3_bucket_has_ignore_public_acls(s3_client, config):
    response = s3_client.get_public_access_block(Bucket=config['website_fqdn'])
    config_block = response['PublicAccessBlockConfiguration']
    assert config_block['IgnorePublicAcls'] is True


def test_s3_bucket_has_restrict_public_buckets(s3_client, config):
    response = s3_client.get_public_access_block(Bucket=config['website_fqdn'])
    config_block = response['PublicAccessBlockConfiguration']
    assert config_block['RestrictPublicBuckets'] is True


def test_s3_bucket_has_encryption(s3_client, config):
    response = s3_client.get_bucket_encryption(Bucket=config['website_fqdn'])
    rules = response['ServerSideEncryptionConfiguration']['Rules']
    assert len(rules) > 0


def test_s3_bucket_encryption_is_aes256(s3_client, config):
    response = s3_client.get_bucket_encryption(Bucket=config['website_fqdn'])
    rules = response['ServerSideEncryptionConfiguration']['Rules']
    algorithm = rules[0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
    assert algorithm == 'AES256'


def test_s3_bucket_has_versioning_disabled(s3_client, config):
    response = s3_client.get_bucket_versioning(Bucket=config['website_fqdn'])
    status = response.get('Status', 'Disabled')
    assert status != 'Enabled'


def test_s3_bucket_has_logging_enabled(s3_client, config):
    response = s3_client.get_bucket_logging(Bucket=config['website_fqdn'])
    assert 'LoggingEnabled' in response


def test_s3_bucket_logging_target_is_central_logs(s3_client, config):
    response = s3_client.get_bucket_logging(Bucket=config['website_fqdn'])
    target_bucket = response['LoggingEnabled']['TargetBucket']
    assert config['central_logs_bucket'] in target_bucket


def test_s3_bucket_has_index_html(s3_client, config):
    response = s3_client.head_object(Bucket=config['website_fqdn'], Key='index.html')
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200
