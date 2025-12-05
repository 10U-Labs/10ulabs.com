"""Pytest fixtures for ECR post-deployment tests."""
import boto3
import pytest


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(config):
    """Provide the AWS region from config."""
    return config["aws_region"]


@pytest.fixture(name="ecr_client", scope="module")
def ecr_client_fixture(aws_region):
    """Provide an ECR client for the configured region."""
    return boto3.client("ecr", region_name=aws_region)
