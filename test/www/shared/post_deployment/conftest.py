"""Pytest fixtures for www shared post-deployment tests.

Note: s3_client is provided by test_fixtures.aws via test/www/conftest.py.
Only www_shared-specific clients are defined here.
"""
import boto3
import pytest


@pytest.fixture(name="cloudfront_client", scope="session")
def cloudfront_client_fixture():
    """Provide CloudFront client (global service, no region needed)."""
    return boto3.client("cloudfront")


@pytest.fixture(name="acm_client", scope="session")
def acm_client_fixture():
    """Provide ACM client for us-east-1 (required for CloudFront certs)."""
    return boto3.client("acm", region_name="us-east-1")


@pytest.fixture(name="route53_client", scope="session")
def route53_client_fixture():
    """Provide Route53 client (global service, no region needed)."""
    return boto3.client("route53")
