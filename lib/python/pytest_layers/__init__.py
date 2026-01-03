"""Pytest layer-based test organization and tracking.

Usage:
    Add pytest_plugins = ['pytest_layers'] to conftest.py

Then mark test files with:
    pytestmark = pytest.mark.layer(N)

Layers are used to categorize tests but do not affect execution order or skip
tests. All tests run regardless of failures in other layers.
"""
from typing import Dict

import pytest


_layer_results: Dict[int, Dict[str, int]] = {}


def pytest_configure(config):
    """Register the layer marker."""
    config.addinivalue_line(
        "markers",
        "layer(num): mark test as belonging to layer N (for organization and tracking)"
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
    """Placeholder for layer-based test setup (skipping disabled)."""
    del item  # Required by hook signature but unused
