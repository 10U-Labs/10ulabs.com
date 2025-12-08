"""Tests to validate www_shared infrastructure exists before api_backend deployment."""


def test_www_shared_s3_bucket_exists(s3_client, www_shared_outputs):
    """Verify the www_shared S3 bucket exists."""
    bucket_name = www_shared_outputs.get("website_bucket_name")
    assert bucket_name, "website_bucket_name output not found in www_shared"
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_www_shared_cloudfront_distribution_exists(cloudfront_client, www_shared_outputs):
    """Verify the www_shared CloudFront distribution exists."""
    distribution_id = www_shared_outputs.get("cloudfront_distribution_id")
    assert distribution_id, "cloudfront_distribution_id output not found in www_shared"
    response = cloudfront_client.get_distribution(Id=distribution_id)
    assert response["Distribution"]["Id"] == distribution_id


def test_www_shared_acm_certificate_exists(acm_client, www_shared_outputs):
    """Verify the www_shared ACM certificate exists and is issued."""
    cert_arn = www_shared_outputs.get("acm_certificate_arn")
    assert cert_arn, "acm_certificate_arn output not found in www_shared"
    response = acm_client.describe_certificate(CertificateArn=cert_arn)
    assert response["Certificate"]["Status"] == "ISSUED"
