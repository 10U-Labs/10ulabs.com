"""Pytest fixtures for api_backend pre-deployment integration tests."""

import re
from typing import Dict

from test.api.conftest import REPO_ROOT, terraform_init, terraform_output

import pytest

# Import AWS fixtures from shared test fixtures
pytest_plugins = ['test_fixtures.aws']


# Layer-based test dependency tracking
# Layer N tests are skipped if any test in layers 1 through N-1 failed
_layer_results: Dict[int, Dict[str, int]] = {}


def pytest_configure(config):
    """Register the layer marker."""
    config.addinivalue_line(
        "markers",
        "layer(num): mark test as belonging to layer N (skips if earlier layers failed)"
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, _call):
    """Track pass/fail results for each layer."""
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
    """Skip tests if any earlier layer failed."""
    for marker in item.iter_markers("layer"):
        layer_num = marker.args[0]
        for prev_layer in range(1, layer_num):
            if prev_layer in _layer_results and _layer_results[prev_layer]["failed"] > 0:
                pytest.skip(f"Skipped: layer {prev_layer} had failures")


BOOTSTRAP_DIR = REPO_ROOT / "src" / "bootstrap"


@pytest.fixture(scope="session", name="bootstrap_initialized")
def bootstrap_initialized_fixture():
    """Initialize terraform for bootstrap state access."""
    return terraform_init(BOOTSTRAP_DIR)


@pytest.fixture(scope="session", name="bootstrap_outputs")
def bootstrap_outputs_fixture(bootstrap_initialized):
    """Get bootstrap terraform outputs."""
    if not bootstrap_initialized:
        pytest.skip("Terraform init failed for bootstrap")
    return {
        "arn_for_central_logs_bucket": terraform_output(
            BOOTSTRAP_DIR, "arn_for_central_logs_bucket"
        ),
        "arn_for_github_actions_role": terraform_output(
            BOOTSTRAP_DIR, "arn_for_github_actions_role"
        ),
        "arn_for_state_bucket": terraform_output(
            BOOTSTRAP_DIR, "arn_for_state_bucket"
        ),
    }


@pytest.fixture(scope="session", name="central_logs_bucket_name")
def central_logs_bucket_name_fixture(bootstrap_outputs):
    """Extract the central logs bucket name from its ARN."""
    arn = bootstrap_outputs.get("arn_for_central_logs_bucket", "")
    if not arn:
        return ""
    match = re.match(r"arn:aws:s3:::(.+)$", arn)
    return match.group(1) if match else ""
