"""Pytest fixtures for pre-deployment integration tests."""
import boto3
import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import create_www_common_fixtures


@pytest.fixture(scope="session")
def sts_client(aws_region):
    """Create an STS client for authentication tests."""
    return boto3.client("sts", region_name=aws_region)


@pytest.fixture(scope="session")
def s3_client(aws_region):
    """Create an S3 client."""
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(scope="session")
def cloudfront_client(aws_region):
    """Create a CloudFront client."""
    return boto3.client("cloudfront", region_name=aws_region)


def _get_cloudfront_distribution(client, outputs):
    """Get CloudFront distribution details (helper function)."""
    distribution_id = outputs.get("cloudfront_distribution_id")
    if not distribution_id:
        return None
    try:
        response = client.get_distribution(Id=distribution_id)
        return response["Distribution"]
    except ClientError:
        return None


@pytest.fixture(scope="module")
def cloudfront_distribution(request):
    """Get CloudFront distribution details."""
    cf_client = request.getfixturevalue("cloudfront_client")
    outputs = request.getfixturevalue("www_common_outputs")
    return _get_cloudfront_distribution(cf_client, outputs)


# Create www_common fixtures with CloudFront and website domain
www_common_terraform_initialized, www_common_outputs = create_www_common_fixtures(
    include_cloudfront=True,
    include_website_domain=True,
)
