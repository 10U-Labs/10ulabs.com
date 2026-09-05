from typing import Any, Dict

import pytest
from test_fixtures.aws import get_log_group_info


@pytest.fixture(scope="module")
def health_handler_log_group(logs_client: Any, config: Dict[str, Any]) -> Any:
    function_name = config.get(
        'health_handler_function_name', 'TenULabsHealthHandler'
    )
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(scope="module")
def health_handler_configuration(lambda_client: Any, config: Dict[str, Any]) -> Any:
    function_name = config.get(
        'health_handler_function_name', 'TenULabsHealthHandler'
    )
    response = lambda_client.get_function(FunctionName=function_name)
    return response["Configuration"]
