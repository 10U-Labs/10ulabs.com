"""Mock utilities for boto3/botocore testing."""
from typing import Any, Callable
from unittest.mock import MagicMock

from botocore.exceptions import ClientError


def create_client_error(
    error_code: str,
    operation_name: str = 'TestOperation'
) -> ClientError:
    """Create a ClientError for testing error handling.

    Args:
        error_code: AWS error code (e.g., 'ResourceNotFoundException').
        operation_name: Name of the AWS operation that failed.

    Returns:
        ClientError exception with the specified error code.
    """
    return ClientError(
        {
            'Error': {
                'Code': error_code,
                'Message': f'Test error: {error_code}'
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
    """Create a boto3.client mock that returns different mocks per service.

    Args:
        ec2_mock: Mock to return for 'ec2' service.
        ssm_mock: Mock to return for 'ssm' service.
        **kwargs: Additional service_name -> mock mappings.

    Returns:
        Function suitable for use as boto3.client side_effect.
    """
    service_mocks = {'ec2': ec2_mock, 'ssm': ssm_mock, **kwargs}

    def mock_client(service_name: str) -> Any:
        return service_mocks.get(service_name, MagicMock())

    return mock_client


def create_boto_client_mock(**service_mocks: Any) -> Callable:
    """Create a boto3 client mock with configurable service mocks.

    Args:
        **service_mocks: Mapping of service names to mock objects.

    Returns:
        Function suitable for use as boto3.client side_effect.
    """
    def mock_client(service_name: str) -> Any:
        return service_mocks.get(service_name, MagicMock())

    return mock_client


def create_mock_lambda_list_mappings_error() -> MagicMock:
    """Create a Lambda mock that errors on list_event_source_mappings.

    Returns:
        MagicMock configured to raise ClientError on list_event_source_mappings.
    """
    mock_lambda = MagicMock()
    mock_lambda.list_event_source_mappings.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable'}},
        'ListEventSourceMappings'
    )
    return mock_lambda


def create_mock_lambda_put_concurrency_error() -> MagicMock:
    """Create a Lambda mock that errors on put_function_concurrency.

    Returns:
        MagicMock configured to raise ClientError on put_function_concurrency.
    """
    mock_lambda = MagicMock()
    mock_lambda.put_function_concurrency.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable'}},
        'PutFunctionConcurrency'
    )
    return mock_lambda


def create_mock_sns_publish_error() -> MagicMock:
    """Create an SNS mock that errors on publish.

    Returns:
        MagicMock configured to raise ClientError on publish.
    """
    mock_sns = MagicMock()
    mock_sns.publish.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable'}},
        'Publish'
    )
    return mock_sns


def create_mock_lambda_with_mappings() -> MagicMock:
    """Create a Lambda mock with enabled event source mappings.

    Returns:
        MagicMock configured to return enabled event source mappings.
    """
    mock_lambda = MagicMock()
    mock_lambda.list_event_source_mappings.return_value = {
        'EventSourceMappings': [{'UUID': 'test-uuid', 'State': 'Enabled'}]
    }
    return mock_lambda


def create_mock_lambda_with_disabled_mappings() -> MagicMock:
    """Create a Lambda mock with disabled event source mappings.

    Returns:
        MagicMock configured to return disabled event source mappings.
    """
    mock_lambda = MagicMock()
    mock_lambda.list_event_source_mappings.return_value = {
        'EventSourceMappings': [{'UUID': 'test-uuid', 'State': 'Disabled'}]
    }
    return mock_lambda


def create_mock_lambda_delete_concurrency_error() -> MagicMock:
    """Create a Lambda mock that errors on delete_function_concurrency.

    Returns:
        MagicMock configured to raise ClientError on delete_function_concurrency.
    """
    mock_lambda = MagicMock()
    mock_lambda.delete_function_concurrency.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable'}},
        'DeleteFunctionConcurrency'
    )
    return mock_lambda
