"""Shared pytest fixtures and utilities for API tests."""
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock

import boto3
import pytest
import requests

# Import canonical label values from runner_labels (single source of truth)
from repo_utils import REPO_ROOT
from runner_labels import (
    DEFAULT_ECS_ARCH,
    DEFAULT_EC2_ARCH,
    DEFAULT_ECS_COMPUTE,
    DEFAULT_EC2_COMPUTE,
    DEFAULT_PRICING,
    DEFAULT_RUNNER_ID,
)
from test_fixtures.terraform import terraform_init, terraform_output

pytest_plugins = ['test_fixtures.aws']

# Common directory constants
API_BACKEND_DIR = REPO_ROOT / "src" / "api" / "shared" / "routing"
API_SHARED_ROUTING_DIR = REPO_ROOT / "src" / "api" / "shared" / "routing"
ECS_RUNNER_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ecs"


def get_runners_outputs(directory: Path) -> Dict[str, str]:
    """Get runners terraform outputs from the specified directory.

    Args:
        directory: Path to the runners terraform directory.

    Returns:
        Dictionary with vpc_id, vpc_public_subnet_ids, and runner_security_group_id.
    """
    return {
        "vpc_id": terraform_output(directory, "vpc_id"),
        "vpc_public_subnet_ids": terraform_output(directory, "vpc_public_subnet_ids"),
        "runner_security_group_id": terraform_output(
            directory, "runner_security_group_id"
        ),
    }


@pytest.fixture(scope="session")
def api_shared_routing_terraform_initialized():
    """Initialize terraform for api_shared_routing state access."""
    return terraform_init(API_SHARED_ROUTING_DIR)


@pytest.fixture(scope="session")
def api_shared_routing_outputs(request):
    """Get api_shared_routing terraform outputs.

    Single source of truth for api_shared_routing output names.
    """
    if not request.getfixturevalue("api_shared_routing_terraform_initialized"):
        pytest.skip("Terraform init failed for api_shared_routing")
    return {
        "api_gateway_rest_api_id": terraform_output(
            API_SHARED_ROUTING_DIR, "api_gateway_rest_api_id"
        ),
    }


@pytest.fixture(scope="session")
def ecs_runner_terraform_initialized():
    """Initialize terraform for ecs_runner state access."""
    return terraform_init(ECS_RUNNER_DIR)


@pytest.fixture(scope="session")
def ecs_runner_outputs(request):
    """Get ecs_runner terraform outputs.

    Single source of truth for ecs_runner output names.
    """
    if not request.getfixturevalue("ecs_runner_terraform_initialized"):
        pytest.skip("Terraform init failed for ecs_runner")
    return {
        "lambda_function_arn": terraform_output(
            ECS_RUNNER_DIR, "lambda_function_arn"
        ),
        "lambda_function_name": terraform_output(
            ECS_RUNNER_DIR, "lambda_function_name"
        ),
        "cluster_arn": terraform_output(ECS_RUNNER_DIR, "cluster_arn"),
        "cluster_name": terraform_output(ECS_RUNNER_DIR, "cluster_name"),
        "task_definition_arn": terraform_output(
            ECS_RUNNER_DIR, "task_definition_arn"
        ),
    }


@pytest.fixture(scope="session")
def apigateway_client(aws_region):
    """Create an API Gateway client."""
    return boto3.client("apigateway", region_name=aws_region)


@pytest.fixture(scope="session")
def ses_client(aws_region):
    """Create an SES client."""
    return boto3.client("ses", region_name=aws_region)


def get_composite_labels(
    platform: str = "ecs",
    compute: str = DEFAULT_ECS_COMPUTE,
    architecture: str | None = None,
    pricing: str = DEFAULT_PRICING,
    runner_id: str = DEFAULT_RUNNER_ID
) -> List[str]:
    """Generate composite runner labels for testing.

    Args:
        platform: Platform type ('ecs' or 'ec2')
        compute: Compute type (ECS: 'fargate'; EC2: 'general-purpose',
                 'memory-optimized', 'gpu', 'fpga')
        architecture: Architecture label (ECS: 'x86', 'arm';
                      EC2: 'intel', 'amd', 'arm' - required for general-purpose
                      and memory-optimized)
        pricing: Pricing model ('spot' or 'on-demand')
        runner_id: Runner ID label (e.g., 'runner-12345')

    Returns:
        List of composite labels.
    """
    labels = [platform, compute, pricing, runner_id]
    if architecture:
        labels.insert(2, architecture)
    return labels


def get_runner_labels() -> Dict[str, List[str]]:
    """Get runner labels as composite label lists for testing.

    Uses canonical values from runner_labels module (single source of truth).

    Returns dict with keys mapping to composite label lists:
        - ec2: EC2 memory-optimized intel spot labels
        - fargate: ECS fargate x86 spot labels
        - ec2_e2e_test: EC2 memory-optimized intel spot labels with e2e marker
        - fargate_e2e_test: ECS fargate x86 spot labels with e2e marker
    """
    return {
        'ec2': [
            'ec2', DEFAULT_EC2_COMPUTE, DEFAULT_EC2_ARCH, DEFAULT_PRICING,
            DEFAULT_RUNNER_ID,
        ],
        'fargate': [
            'ecs', DEFAULT_ECS_COMPUTE, DEFAULT_ECS_ARCH, DEFAULT_PRICING,
            DEFAULT_RUNNER_ID,
        ],
        'ec2_e2e_test': [
            'ec2', DEFAULT_EC2_COMPUTE, DEFAULT_EC2_ARCH, DEFAULT_PRICING,
            DEFAULT_RUNNER_ID, 'e2e',
        ],
        'fargate_e2e_test': [
            'ecs', DEFAULT_ECS_COMPUTE, DEFAULT_ECS_ARCH, DEFAULT_PRICING,
            DEFAULT_RUNNER_ID, 'e2e',
        ],
    }


def endpoint_is_deployed(api_url: str, path: str, method: str = "GET") -> bool:
    """Check if an endpoint is deployed and functional.

    Returns False if:
    - Endpoint returns 404 (not deployed)
    - Endpoint returns "Not Found" error in JSON (CatchAllHandler)
    - Endpoint returns 500 (Lambda not properly deployed/configured)
    """
    url = f"{api_url}{path}"
    headers = {"x-test-mode": "true"}
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        else:
            response = requests.post(url, headers=headers, json={}, timeout=5)
        if response.status_code == 404:
            return False
        if response.status_code == 500:
            return False
        try:
            body = response.json()
            if body.get("error") == "Not Found":
                return False
        except (ValueError, KeyError):
            pass
        return True
    except requests.exceptions.RequestException:
        return False


def skip_if_endpoint_not_deployed(api_url: str, path: str, method: str = "GET"):
    """Skip test if the specified endpoint is not deployed."""
    if not endpoint_is_deployed(api_url, path, method):
        pytest.skip(f"Endpoint {path} not deployed (managed by separate workflow)")


@pytest.fixture
def lambda_context():
    """Provide a mock Lambda context object."""
    return Mock()


@pytest.fixture(scope="session")
def lambda_client(aws_region):
    """Provide a Lambda client for the configured AWS region."""
    return boto3.client("lambda", region_name=aws_region)
