"""Pytest layer-based test dependency tracking.

Usage:
    Add pytest_plugins = ['pytest_layers'] to conftest.py

Then mark test files with:
    pytestmark = pytest.mark.layer(N)

Layer N tests automatically skip if any test in layers 1 through N-1 failed.
"""
from typing import Dict

import pytest


_layer_results: Dict[int, Dict[str, int]] = {}


def pytest_configure(config):
    """Register the layer marker."""
    config.addinivalue_line(
        "markers",
        "layer(num): mark test as belonging to layer N (skips if earlier layers failed)"
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Track pass/fail results for each layer."""
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
    """Skip tests if any earlier layer failed."""
    for marker in item.iter_markers("layer"):
        layer_num = marker.args[0]
        for prev_layer in range(1, layer_num):
            if prev_layer in _layer_results and _layer_results[prev_layer]["failed"] > 0:
                pytest.skip(f"Skipped: layer {prev_layer} had failures")
