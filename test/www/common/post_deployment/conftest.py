import boto3
import pytest


@pytest.fixture(scope="session")
def cloudfront_client():
    return boto3.client("cloudfront")


@pytest.fixture(scope="session")
def acm_client():
    return boto3.client("acm", region_name="us-east-1")


@pytest.fixture(scope="session")
def route53_client():
    return boto3.client("route53")
