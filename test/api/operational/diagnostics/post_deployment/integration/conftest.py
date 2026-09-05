from typing import Any, Dict

import boto3
import pytest
from test_fixtures.aws import get_log_group_info


@pytest.fixture(scope="session")
def iam_client(aws_region: str) -> Any:
    return boto3.client("iam", region_name=aws_region)


@pytest.fixture(scope="module")
def diagnostics_handler_log_group(logs_client: Any, config: Dict[str, Any]) -> Any:
    function_name = config.get(
        'diagnostics_handler_function_name', 'TenULabsDiagnosticsHandler'
    )
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(scope="module")
def diagnostics_handler_configuration(
    lambda_client: Any,
    config: Dict[str, Any]
) -> Any:
    function_name = config.get(
        'diagnostics_handler_function_name', 'TenULabsDiagnosticsHandler'
    )
    response = lambda_client.get_function(FunctionName=function_name)
    return response["Configuration"]
