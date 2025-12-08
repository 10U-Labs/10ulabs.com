"""Tests to validate www_shared infrastructure exists for www index."""


def test_www_shared_terraform_outputs_readable(www_shared_outputs):
    """Verify www_shared terraform outputs are accessible."""
    assert www_shared_outputs.get("bucket_name"), \
        "bucket_name output not found in www_shared"
    assert www_shared_outputs.get("website_domain_name"), \
        "website_domain_name output not found in www_shared"
    assert www_shared_outputs.get("cloudfront_distribution_id"), \
        "cloudfront_distribution_id output not found in www_shared"


def test_s3_bucket_exists(s3_client, www_shared_outputs):
    """Verify the S3 bucket exists."""
    bucket_name = www_shared_outputs.get("bucket_name")
    assert bucket_name, "bucket_name output not found"

    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_cloudfront_distribution_exists(cloudfront_client, www_shared_outputs):
    """Verify the CloudFront distribution exists."""
    distribution_id = www_shared_outputs.get("cloudfront_distribution_id")
    assert distribution_id, "cloudfront_distribution_id output not found"

    response = cloudfront_client.get_distribution(Id=distribution_id)
    assert response["Distribution"]["Id"] == distribution_id
    assert response["Distribution"]["Status"] == "Deployed"
