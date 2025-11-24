def test_s3_docs_bucket_exists(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_s3_bucket_versioning_disabled(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert response.get("Status") != "Enabled"


def test_s3_bucket_encryption_enabled(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert "ServerSideEncryptionConfiguration" in response
    assert "Rules" in response["ServerSideEncryptionConfiguration"]


def test_index_html_in_s3(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.head_object(Bucket=bucket_name, Key="index.html")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_openapi_yml_in_s3(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.head_object(Bucket=bucket_name, Key="openapi.yml")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
