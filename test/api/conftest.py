"""Shared pytest fixtures and utilities for API tests."""
from typing import Dict, List
from unittest.mock import Mock

import pytest
import requests


def get_composite_labels(
    platform: str = "ecs",
    compute: str = "fargate",
    pricing: str = "spot",
    runner_id: str = "runner-12345"
) -> List[str]:
    """Generate composite runner labels for testing.

    Args:
        platform: Platform type ('ecs' or 'ec2')
        compute: Compute type ('fargate', 'r8i', 'g6e')
        pricing: Pricing model ('spot' or 'on-demand')
        runner_id: Runner ID label (e.g., 'runner-12345')

    Returns:
        List of composite labels.
    """
    return [platform, compute, pricing, runner_id]


def get_runner_labels() -> Dict[str, List[str]]:
    """Get runner labels as composite label lists for testing.

    Returns dict with keys mapping to composite label lists:
        - ec2: EC2 r8i spot labels
        - fargate: ECS fargate spot labels
        - ec2_e2e_test: EC2 r8i spot labels with e2e marker
        - fargate_e2e_test: ECS fargate spot labels with e2e marker
    """
    return {
        'ec2': ['ec2', 'r8i', 'spot', 'runner-12345'],
        'fargate': ['ecs', 'fargate', 'spot', 'runner-12345'],
        'ec2_e2e_test': ['ec2', 'r8i', 'spot', 'runner-12345', 'e2e'],
        'fargate_e2e_test': ['ecs', 'fargate', 'spot', 'runner-12345', 'e2e'],
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
    import boto3
    return boto3.client("lambda", region_name=aws_region)
