"""Tests to validate S3 bucket exists for rack_designer designs."""


def test_www_shared_terraform_outputs_readable(www_shared_outputs):
    """Verify www_shared terraform outputs are accessible."""
    assert www_shared_outputs.get("bucket_name"), \
        "bucket_name output not found in www_shared"


def test_s3_bucket_exists(s3_client, www_shared_outputs):
    """Verify the S3 bucket for designs exists."""
    bucket_name = www_shared_outputs.get("bucket_name")
    assert bucket_name, "bucket_name output not found"

    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
