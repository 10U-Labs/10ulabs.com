"""Pytest fixtures for simulation-soc integration tests."""
import pytest

from test_fixtures.aws import get_log_group_info


pytest_plugins = ['pytest_layers']


@pytest.fixture(name="handler_log_group", scope="module")
def handler_log_group_fixture(logs_client, shared_config):
    """Get the simulation-soc handler log group info from CloudWatch."""
    function_name = shared_config.get("lambda_handler_names", {}).get(
        "simulation_soc", "TenULabsSimulationSocHandler"
    )
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)
