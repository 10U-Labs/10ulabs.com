"""Pytest fixtures for www shared post-deployment tests."""
import boto3
import pytest


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(config):
    """Provide AWS region from config."""
    return config["aws_region"]


@pytest.fixture(name="s3_client", scope="module")
def s3_client_fixture(aws_region):
    """Provide S3 client for the configured region."""
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(name="cloudfront_client", scope="module")
def cloudfront_client_fixture():
    """Provide CloudFront client."""
    return boto3.client("cloudfront")


@pytest.fixture(name="acm_client", scope="module")
def acm_client_fixture():
    """Provide ACM client for us-east-1 region."""
    return boto3.client("acm", region_name="us-east-1")


@pytest.fixture(name="route53_client", scope="module")
def route53_client_fixture():
    """Provide Route53 client."""
    return boto3.client("route53")
