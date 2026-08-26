def test_acm_certificate_is_issued(acm_client):
    certificates = acm_client.list_certificates(CertificateStatuses=["ISSUED"])
    assert len(certificates["CertificateSummaryList"]) >= 0


def test_cloudfront_logging_enabled(logging_config):
    assert logging_config.get("Enabled", False) is True


def test_cloudfront_logging_bucket_is_central_logs(logging_config, config):
    bucket = logging_config.get("Bucket", "")
    assert config["central_logs_bucket"] in bucket


def test_cloudfront_logging_prefix_is_correct(logging_config):
    prefix = logging_config.get("Prefix", "")
    assert prefix == "cloudfront-logs/website/"


def test_cloudfront_logging_excludes_cookies(logging_config):
    assert logging_config.get("IncludeCookies", True) is False


def test_cloudfront_uses_https_redirect(default_cache_behavior):
    policy = default_cache_behavior["ViewerProtocolPolicy"]
    assert policy == "redirect-to-https"


def test_cloudfront_compression_enabled(default_cache_behavior):
    assert default_cache_behavior.get("Compress", False) is True


def test_s3_bucket_blocks_public_acls(public_access_block):
    assert public_access_block["BlockPublicAcls"] is True


def test_s3_bucket_blocks_public_policy(public_access_block):
    assert public_access_block["BlockPublicPolicy"] is True


def test_s3_bucket_ignores_public_acls(public_access_block):
    assert public_access_block["IgnorePublicAcls"] is True


def test_s3_bucket_restricts_public_buckets(public_access_block):
    assert public_access_block["RestrictPublicBuckets"] is True


def test_s3_bucket_has_encryption(s3_client, config):
    response = s3_client.get_bucket_encryption(Bucket=config["website_bucket_name"])
    rules = response["ServerSideEncryptionConfiguration"]["Rules"]
    assert len(rules) > 0


def test_s3_bucket_encryption_is_aes256(s3_client, config):
    response = s3_client.get_bucket_encryption(Bucket=config["website_bucket_name"])
    rules = response["ServerSideEncryptionConfiguration"]["Rules"]
    algorithm = rules[0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]
    assert algorithm == "AES256"


def test_s3_bucket_versioning_disabled(s3_client, config):
    response = s3_client.get_bucket_versioning(Bucket=config["website_bucket_name"])
    status = response.get("Status", "Disabled")
    assert status != "Enabled"


def test_s3_bucket_has_logging_enabled(s3_client, config):
    response = s3_client.get_bucket_logging(Bucket=config["website_bucket_name"])
    assert "LoggingEnabled" in response


def test_s3_bucket_logging_target_is_central_logs(s3_client, config):
    response = s3_client.get_bucket_logging(Bucket=config["website_bucket_name"])
    target_bucket = response["LoggingEnabled"]["TargetBucket"]
    assert config["central_logs_bucket"] in target_bucket


def test_lambda_edge_runtime_is_python312(spa_routing_lambda_config):
    runtime = spa_routing_lambda_config.get("Runtime", "")
    assert runtime == "python3.12"


def test_lambda_edge_timeout_is_5_seconds(spa_routing_lambda_config):
    timeout = spa_routing_lambda_config.get("Timeout", 0)
    assert timeout == 5


def test_lambda_edge_memory_is_128mb(spa_routing_lambda_config):
    memory = spa_routing_lambda_config.get("MemorySize", 0)
    assert memory == 128


def test_lambda_edge_handler_is_correct(spa_routing_lambda_config):
    handler = spa_routing_lambda_config.get("Handler", "")
    assert handler == "handler.lambda_handler"


def test_lambda_edge_has_description(spa_routing_lambda_config):
    description = spa_routing_lambda_config.get("Description", "")
    assert len(description) > 0
