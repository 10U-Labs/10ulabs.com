"""Layer 2: Configuration tests for simulation-soc endpoint.

Verify that resources created by this deployment are configured correctly.
"""



class TestSimulationSocCloudWatchLogsConfiguration:
    """Layer 2: Verify simulation-soc CloudWatch log group is configured correctly."""

    def test_simulation_soc_handler_log_group_has_retention_policy(
        self, handler_log_group
    ):
        """Verify simulation-soc log group has retention policy."""
        assert handler_log_group["retention"] is not None, (
            f"Simulation SOC log group '{handler_log_group['name']}' "
            "must have retention configured"
        )

    def test_simulation_soc_handler_log_group_retention_matches_policy(
        self, handler_log_group
    ):
        """Verify simulation-soc log group uses 7-day retention per standards."""
        retention = handler_log_group["retention"]
        assert retention == 7, (
            f"Simulation SOC log group retention is {retention} days, expected 7"
        )
