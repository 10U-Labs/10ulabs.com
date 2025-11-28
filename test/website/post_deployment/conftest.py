import boto3
import pytest


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(config):
    return config["aws_region"]


@pytest.fixture(name="s3_client", scope="module")
def s3_client_fixture(aws_region):
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(name="cloudfront_client", scope="module")
def cloudfront_client_fixture():
    return boto3.client("cloudfront")


@pytest.fixture(name="acm_client", scope="module")
def acm_client_fixture():
    return boto3.client("acm", region_name="us-east-1")


@pytest.fixture(name="route53_client", scope="module")
def route53_client_fixture():
    return boto3.client("route53")
