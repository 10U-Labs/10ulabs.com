"""Pytest fixtures for cloudfront_waf module tests."""
import pytest


@pytest.fixture(name="module_path")
def fixture_module_path(modules_dir):
    """Provide path to cloudfront_waf module directory."""
    return modules_dir / "cloudfront_waf"
