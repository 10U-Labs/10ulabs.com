"""Pytest fixtures for pre-deployment integration tests."""
import boto3
import pytest
from repo_utils import REPO_ROOT
from test_fixtures.terraform import terraform_init, terraform_output


WWW_SHARED_DIR = REPO_ROOT / "src" / "www" / "shared"


@pytest.fixture(scope="session")
def s3_client(aws_region):
    """Create an S3 client."""
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(scope="session")
def cloudfront_client(aws_region):
    """Create a CloudFront client."""
    return boto3.client("cloudfront", region_name=aws_region)


@pytest.fixture(scope="session")
def www_shared_terraform_initialized():
    """Initialize terraform for www_shared state access."""
    return terraform_init(WWW_SHARED_DIR)


@pytest.fixture(scope="session")
def www_shared_outputs(request):
    """Get www_shared terraform outputs."""
    if not request.getfixturevalue("www_shared_terraform_initialized"):
        pytest.skip("Terraform init failed for www_shared")
    return {
        "bucket_name": terraform_output(
            WWW_SHARED_DIR, "bucket_name"
        ),
        "bucket_arn": terraform_output(
            WWW_SHARED_DIR, "bucket_arn"
        ),
        "website_domain_name": terraform_output(
            WWW_SHARED_DIR, "website_domain_name"
        ),
        "cloudfront_distribution_id": terraform_output(
            WWW_SHARED_DIR, "cloudfront_distribution_id"
        ),
    }
