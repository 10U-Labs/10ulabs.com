"""Pytest fixtures for www shared post-deployment tests."""
import boto3
import pytest


@pytest.fixture(name="cloudfront_client", scope="session")
def cloudfront_client_fixture():
    """Provide CloudFront client."""
    return boto3.client("cloudfront")


@pytest.fixture(name="acm_client", scope="session")
def acm_client_fixture():
    """Provide ACM client for us-east-1 region."""
    return boto3.client("acm", region_name="us-east-1")


@pytest.fixture(name="route53_client", scope="session")
def route53_client_fixture():
    """Provide Route53 client."""
    return boto3.client("route53")


@pytest.fixture(name="s3_client", scope="session")
def s3_client_fixture():
    """Provide S3 client."""
    return boto3.client("s3")
