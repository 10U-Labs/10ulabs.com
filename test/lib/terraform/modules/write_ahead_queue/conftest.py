"""Pytest fixtures for write_ahead_queue module tests."""
import pytest


@pytest.fixture(name="module_path")
def fixture_module_path(modules_dir):
    """Provide path to write_ahead_queue module directory."""
    return modules_dir / "write_ahead_queue"
