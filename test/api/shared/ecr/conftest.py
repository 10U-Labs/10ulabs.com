"""Pytest fixtures for ECR tests."""
import os
import re

import boto3
import pytest


BASE_DIR = os.path.join(os.path.dirname(__file__), '../../../../src/api/shared/ecr')
SHARED_OUTPUTS_PATH = os.path.join(
    os.path.dirname(__file__), '../../../../lib/terraform/outputs.tf'
)


def parse_tf_output(file_path, output_name):
    """Parse a Terraform output value from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = rf'output\s+"{output_name}"\s*\{{\s*value\s*=\s*"([^"]+)"'
    match = re.search(pattern, content)
    return match.group(1) if match else None


@pytest.fixture(name="aws_region", scope="session")
def aws_region_fixture():
    """Provide the AWS region from Terraform outputs."""
    return parse_tf_output(SHARED_OUTPUTS_PATH, "aws_region")


@pytest.fixture(name="ecr_client", scope="session")
def ecr_client_fixture(aws_region):
    """Provide an ECR client for the configured region."""
    return boto3.client('ecr', region_name=aws_region)


@pytest.fixture(name="config", scope="session")
def config_fixture():
    """Provide configuration values from Terraform outputs."""
    return {
        "aws_region": parse_tf_output(SHARED_OUTPUTS_PATH, "aws_region"),
        "ecr_repository_name": parse_tf_output(SHARED_OUTPUTS_PATH, "ecr_repository_name"),
    }


@pytest.fixture(name="ecr_dir", scope="session")
def ecr_dir_fixture():
    """Provide the path to the ECR Terraform directory."""
    return BASE_DIR


@pytest.fixture(name="ecr_repository_name", scope="session")
def ecr_repository_name_fixture():
    """Provide the ECR repository name from Terraform outputs."""
    return parse_tf_output(SHARED_OUTPUTS_PATH, "ecr_repository_name")
