from typing import Any, Dict

import pytest

from test_fixtures.aws import get_log_group_info


@pytest.fixture(scope="module")
def contact_handler_function_name(shared_config: Dict[str, Any]) -> str:
    return shared_config.get("lambda_handler_names", {}).get(
        "contact", "TenULabsContactHandler"
    )


@pytest.fixture(scope="module")
def config(request: pytest.FixtureRequest, shared_config: Dict[str, Any]) -> Dict[str, str]:
    function_name = request.getfixturevalue("contact_handler_function_name")
    return {
        "contact_handler_function_name": function_name,
        "resource_prefix": shared_config.get("resource_prefix", "TenULabs"),
    }


@pytest.fixture(scope="module")
def contact_handler_log_group(request: pytest.FixtureRequest, logs_client: Any) -> Any:
    function_name = request.getfixturevalue("contact_handler_function_name")
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(scope="module")
def contact_handler_env_vars(request: pytest.FixtureRequest, lambda_client: Any) -> Any:
    function_name = request.getfixturevalue("contact_handler_function_name")
    response = lambda_client.get_function(FunctionName=function_name)
    return response["Configuration"].get("Environment", {}).get("Variables", {})
