import pytest

from test_fixtures.aws import get_log_group_info


@pytest.fixture(scope="module")
def contact_handler_function_name(shared_config):
    return shared_config.get("lambda_handler_names", {}).get(
        "contact", "TenULabsContactHandler"
    )


@pytest.fixture(scope="module")
def config(request, shared_config):
    function_name = request.getfixturevalue("contact_handler_function_name")
    return {
        "contact_handler_function_name": function_name,
        "resource_prefix": shared_config.get("resource_prefix", "TenULabs"),
    }


@pytest.fixture(scope="module")
def contact_handler_log_group(request, logs_client):
    function_name = request.getfixturevalue("contact_handler_function_name")
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(scope="module")
def contact_handler_env_vars(request, lambda_client):
    function_name = request.getfixturevalue("contact_handler_function_name")
    response = lambda_client.get_function(FunctionName=function_name)
    return response["Configuration"].get("Environment", {}).get("Variables", {})
