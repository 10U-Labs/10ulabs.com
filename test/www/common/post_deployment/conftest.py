"""Pytest fixtures for www shared post-deployment tests.

Note: s3_client is provided by test_fixtures.aws via test/www/conftest.py.
Only www_common-specific clients are defined here.
"""
import boto3
import pytest


@pytest.fixture(scope="session")
def cloudfront_client():
    """Provide CloudFront client (global service, no region needed)."""
    return boto3.client("cloudfront")


@pytest.fixture(scope="session")
def acm_client():
    """Provide ACM client for us-east-1 (required for CloudFront certs)."""
    return boto3.client("acm", region_name="us-east-1")


@pytest.fixture(scope="session")
def route53_client():
    """Provide Route53 client (global service, no region needed)."""
    return boto3.client("route53")
