from typing import Any
from unittest.mock import MagicMock

from lambda_response import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
    assert_cors_headers,
)
from boto_mocks import (
    create_client_error,
    create_multi_client_mock,
    create_boto_client_mock,
    create_mock_lambda_list_mappings_error,
    create_mock_lambda_put_concurrency_error,
    create_mock_sns_publish_error,
    create_mock_lambda_with_mappings,
    create_mock_lambda_with_disabled_mappings,
    create_mock_lambda_delete_concurrency_error,
)
from module_utils import reset_module_state, create_lambda_loader

__all__ = [
    'parse_response_body',
    'assert_response_status',
    'assert_json_content_type',
    'assert_cors_headers',
    'create_client_error',
    'create_multi_client_mock',
    'create_boto_client_mock',
    'create_mock_lambda_list_mappings_error',
    'create_mock_lambda_put_concurrency_error',
    'create_mock_sns_publish_error',
    'create_mock_lambda_with_mappings',
    'create_mock_lambda_with_disabled_mappings',
    'create_mock_lambda_delete_concurrency_error',
    'reset_module_state',
    'create_lambda_loader',
    'create_mock_dynamodb_client',
]


def create_mock_dynamodb_client(method_name: str, return_value: Any = None) -> MagicMock:
    if return_value is None:
        return_value = {}
    mock_client = MagicMock()
    getattr(mock_client, method_name).return_value = return_value
    return mock_client
