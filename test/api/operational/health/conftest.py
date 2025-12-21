"""Pytest fixtures for health endpoint tests.

Implements the layer marker system for integration tests with automatic skip
when earlier layers fail.
"""
import re
from typing import Dict

import boto3
import pytest
from repo_utils import REPO_ROOT

HEALTH_SRC = REPO_ROOT / "src" / "api" / "operational" / "health"

# Track layer results across test session for layer-based skip
_layer_results: Dict[int, Dict[str, int]] = {}


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "layer(num): mark test as belonging to layer N"
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Track pass/fail counts per layer."""
    del call  # Required by hook signature but unused
    outcome = yield
    result = outcome.get_result()

    if result.when == "call":
        for marker in item.iter_markers("layer"):
            layer_num = marker.args[0]
            if layer_num not in _layer_results:
                _layer_results[layer_num] = {"passed": 0, "failed": 0}

            if result.passed:
                _layer_results[layer_num]["passed"] += 1
            elif result.failed:
                _layer_results[layer_num]["failed"] += 1


def pytest_runtest_setup(item):
    """Skip tests if earlier layers failed."""
    for marker in item.iter_markers("layer"):
        layer_num = marker.args[0]
        for prev_layer in range(1, layer_num):
            if _layer_results.get(prev_layer, {}).get("failed", 0) > 0:
                pytest.skip(f"Skipped: layer {prev_layer} had failures")


@pytest.fixture(scope="module")
def logs_client(aws_region):
    """Create a CloudWatch Logs client."""
    return boto3.client("logs", region_name=aws_region)


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Create configuration fixture from terraform.tfvars and shared outputs."""
    tfvars_path = HEALTH_SRC / "terraform.tfvars"
    result: Dict[str, str] = {}
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
                if match:
                    key, value = match.groups()
                    result[key] = value.strip('"')
    result['aws_region'] = shared_config.get('aws_region', 'us-east-1')
    result['api_fqdn'] = f"api.{shared_config.get('domain_name', '')}"
    return result
