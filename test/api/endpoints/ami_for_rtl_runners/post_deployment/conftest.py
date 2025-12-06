"""Shared fixtures for RTL runner post-deployment tests."""

import boto3
import pytest


@pytest.fixture
def ecr_client() -> boto3.client:
    """Return ECR client for image verification."""
    return boto3.client("ecr")


@pytest.fixture
def aws_region() -> str:
    """Return AWS region for RTL runner infrastructure."""
    return "us-east-2"


@pytest.fixture
def ecr_repository_name() -> str:
    """Return ECR repository name for RTL images."""
    return "10ulabs"


@pytest.fixture
def rtl_image_variants() -> list:
    """Return list of RTL image variants."""
    return ["rtl-sim", "rtl-synth", "rtl-gpu"]
