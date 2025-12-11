"""Tests for S3 bucket deployment and configuration."""


def test_s3_docs_bucket_exists(s3_client, config):
    """Verify that the S3 docs bucket exists."""
    bucket_name = config["api_fqdn"]
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_s3_bucket_versioning_disabled(s3_client, config):
    """Verify that S3 bucket versioning is disabled."""
    bucket_name = config["api_fqdn"]
    response = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert response.get("Status") != "Enabled"


def test_s3_bucket_encryption_config_exists(s3_client, config):
    """Verify that S3 bucket encryption configuration exists."""
    bucket_name = config["api_fqdn"]
    response = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert "ServerSideEncryptionConfiguration" in response


def test_s3_bucket_encryption_has_rules(s3_client, config):
    """Verify that S3 bucket encryption has rules defined."""
    bucket_name = config["api_fqdn"]
    response = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert "Rules" in response["ServerSideEncryptionConfiguration"]


def test_index_html_in_s3(s3_client, config):
    """Verify that index.html exists in S3 bucket."""
    bucket_name = config["api_fqdn"]
    response = s3_client.head_object(Bucket=bucket_name, Key="index.html")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_openapi_json_in_s3(s3_client, config):
    """Verify that openapi.json exists in S3 bucket."""
    bucket_name = config["api_fqdn"]
    response = s3_client.head_object(Bucket=bucket_name, Key="openapi.json")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
