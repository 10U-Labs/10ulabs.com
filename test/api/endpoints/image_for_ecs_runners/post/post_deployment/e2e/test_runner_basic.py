"""E2E tests for basic runner functionality using a shared container.

This module uses a single runner container to verify:
- Runner successfully registers with GitHub
- Runner appears online
- Runner has correct labels (including multiple labels)
"""
from .conftest import get_label_by_name


def test_runner_successfully_registers(shared_runner):
    """Test that runner successfully registers with GitHub."""
    assert shared_runner["info"] is not None


def test_runner_is_online(shared_runner):
    """Test that runner shows online status."""
    assert shared_runner["info"]["status"] == "online"


def test_runner_has_first_label(shared_runner):
    """Test that runner has first specified label."""
    labels = shared_runner["info"]["labels"]
    label = get_label_by_name(labels, "e2e-label1")
    assert label is not None


def test_runner_has_second_label(shared_runner):
    """Test that runner has second specified label."""
    labels = shared_runner["info"]["labels"]
    label = get_label_by_name(labels, "e2e-label2")
    assert label is not None


def test_runner_has_third_label(shared_runner):
    """Test that runner has third specified label."""
    labels = shared_runner["info"]["labels"]
    label = get_label_by_name(labels, "e2e-label3")
    assert label is not None
