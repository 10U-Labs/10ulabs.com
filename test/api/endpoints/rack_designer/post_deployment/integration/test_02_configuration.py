"""Layer 2: Configuration tests for rack designer endpoint.

Verify that resources created by this deployment are configured correctly.
"""
import pytest

pytestmark = pytest.mark.layer(2)


class TestRackDesignerCloudWatchLogsConfiguration:
    """Layer 2: Verify rack designer CloudWatch log group is configured correctly."""

    def test_rack_designer_handler_log_group_has_retention_set(
        self, handler_log_group
    ):
        """Verify rack designer log group has retention period configured."""
        assert handler_log_group["retention"] is not None, (
            f"Rack designer log group '{handler_log_group['name']}' "
            "should have retention set"
        )

    def test_rack_designer_handler_log_group_retention_is_7_days(
        self, handler_log_group
    ):
        """Verify rack designer log group retention is 7 days per policy."""
        retention = handler_log_group["retention"]
        assert retention == 7, (
            f"Rack designer log group retention should be 7 days, got: {retention}"
        )
