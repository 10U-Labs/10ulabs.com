from typing import Any, Callable, Optional
from unittest.mock import MagicMock

from botocore.exceptions import ClientError


def create_client_error(
    error_code: str,
    operation_name: str = 'TestOperation',
    message: Optional[str] = None
) -> ClientError:
    return ClientError(
        {
            'Error': {
                'Code': error_code,
                'Message': message or f'Test error: {error_code}'
            },
            'ResponseMetadata': {
                'RequestId': 'test-request-id',
                'HTTPStatusCode': 400,
                'HTTPHeaders': {},
                'RetryAttempts': 0,
                'HostId': ''
            }
        },
        operation_name
    )


def create_multi_client_mock(ec2_mock: Any, ssm_mock: Any, **kwargs: Any) -> Callable:
    service_mocks = {'ec2': ec2_mock, 'ssm': ssm_mock, **kwargs}

    def mock_client(service_name: str) -> Any:
        return service_mocks.get(service_name, MagicMock())

    return mock_client


def create_boto_client_mock(**service_mocks: Any) -> Callable:
    def mock_client(service_name: str) -> Any:
        return service_mocks.get(service_name, MagicMock())

    return mock_client


def create_mock_lambda_list_mappings_error() -> MagicMock:
    mock_lambda = MagicMock()
    mock_lambda.list_event_source_mappings.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable'}},
        'ListEventSourceMappings'
    )
    return mock_lambda


def create_mock_lambda_put_concurrency_error() -> MagicMock:
    mock_lambda = MagicMock()
    mock_lambda.put_function_concurrency.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable'}},
        'PutFunctionConcurrency'
    )
    return mock_lambda


def create_mock_sns_publish_error() -> MagicMock:
    mock_sns = MagicMock()
    mock_sns.publish.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable'}},
        'Publish'
    )
    return mock_sns


def create_mock_lambda_with_mappings() -> MagicMock:
    mock_lambda = MagicMock()
    mock_lambda.list_event_source_mappings.return_value = {
        'EventSourceMappings': [{'UUID': 'test-uuid', 'State': 'Enabled'}]
    }
    return mock_lambda


def create_mock_lambda_with_disabled_mappings() -> MagicMock:
    mock_lambda = MagicMock()
    mock_lambda.list_event_source_mappings.return_value = {
        'EventSourceMappings': [{'UUID': 'test-uuid', 'State': 'Disabled'}]
    }
    return mock_lambda


def create_mock_lambda_delete_concurrency_error() -> MagicMock:
    mock_lambda = MagicMock()
    mock_lambda.delete_function_concurrency.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable'}},
        'DeleteFunctionConcurrency'
    )
    return mock_lambda
