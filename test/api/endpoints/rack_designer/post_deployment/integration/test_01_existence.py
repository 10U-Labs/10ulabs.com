"""Layer 1: Existence tests for rack designer endpoint.

Verify that resources created by this deployment exist.
"""
import pytest

pytestmark = pytest.mark.layer(1)


def test_rack_designer_handler_log_group_exists(handler_log_group):
    """Verify rack designer handler CloudWatch log group exists."""
    assert handler_log_group["exists"], (
        f"CloudWatch log group '{handler_log_group['name']}' does not exist"
    )
