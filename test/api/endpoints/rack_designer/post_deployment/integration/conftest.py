"""Pytest fixtures for rack designer integration tests."""
import pytest

from test_fixtures.aws import get_log_group_info


pytest_plugins = ['pytest_layers']


@pytest.fixture(name="website_url", scope="module")
def website_url_fixture(config):
    """Provide website URL for tests."""
    return f"https://www.{config['domain_name']}"


@pytest.fixture(name="handler_log_group", scope="module")
def handler_log_group_fixture(logs_client, shared_config):
    """Get the rack designer handler log group info from CloudWatch."""
    function_name = shared_config.get("lambda_handler_names", {}).get(
        "rack_designer", "TenULabsRackDesignerHandler"
    )
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(name="test_device_id", scope="module")
def test_device_id_fixture():
    """Provide test device ID for tests."""
    return "integration-test-device"
