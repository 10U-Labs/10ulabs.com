"""Layer 1: Existence tests for simulation-soc endpoint.

Verify that resources created by this deployment exist.
"""



def test_simulation_soc_handler_log_group_exists(handler_log_group):
    """Verify simulation-soc handler CloudWatch log group exists."""
    assert handler_log_group["exists"], (
        f"CloudWatch log group '{handler_log_group['name']}' does not exist"
    )
