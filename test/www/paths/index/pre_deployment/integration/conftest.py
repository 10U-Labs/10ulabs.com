"""Pytest fixtures for pre-deployment integration tests."""
import boto3
import pytest
from test_fixtures.integration import create_www_shared_fixtures


@pytest.fixture(scope="session")
def s3_client(aws_region):
    """Create an S3 client."""
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(scope="session")
def cloudfront_client(aws_region):
    """Create a CloudFront client."""
    return boto3.client("cloudfront", region_name=aws_region)


# Create www_shared fixtures with CloudFront and website domain
www_shared_terraform_initialized, www_shared_outputs = create_www_shared_fixtures(
    include_cloudfront=True,
    include_website_domain=True,
)
