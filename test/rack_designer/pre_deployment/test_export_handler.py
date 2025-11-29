import os
from unittest.mock import patch, MagicMock
import pytest


@pytest.fixture(autouse=True)
def set_env_vars():
    os.environ['DYNAMODB_TABLE_ARN'] = 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events'
    os.environ['S3_BUCKET'] = 'test-bucket'
    os.environ['S3_PREFIX'] = 'exports/events'
    yield
    del os.environ['DYNAMODB_TABLE_ARN']
    del os.environ['S3_BUCKET']
    del os.environ['S3_PREFIX']


@pytest.fixture
def mock_dynamodb():
    with patch('boto3.client') as mock_client:
        mock_dynamodb_client = MagicMock()
        mock_client.return_value = mock_dynamodb_client
        yield mock_dynamodb_client


def test_lambda_handler_returns_status_code_200(mock_dynamodb):
    from src.rack_designer.lambdas.export_handler import lambda_handler
    mock_dynamodb.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    result = lambda_handler({}, None)
    assert result['statusCode'] == 200


def test_lambda_handler_calls_export_table_to_point_in_time(mock_dynamodb):
    from src.rack_designer.lambdas.export_handler import lambda_handler
    mock_dynamodb.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    lambda_handler({}, None)
    assert mock_dynamodb.export_table_to_point_in_time.called


def test_lambda_handler_uses_correct_table_arn(mock_dynamodb):
    from src.rack_designer.lambdas.export_handler import lambda_handler
    mock_dynamodb.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    lambda_handler({}, None)
    call_kwargs = mock_dynamodb.export_table_to_point_in_time.call_args[1]
    assert call_kwargs['TableArn'] == 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events'


def test_lambda_handler_uses_correct_s3_bucket(mock_dynamodb):
    from src.rack_designer.lambdas.export_handler import lambda_handler
    mock_dynamodb.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    lambda_handler({}, None)
    call_kwargs = mock_dynamodb.export_table_to_point_in_time.call_args[1]
    assert call_kwargs['S3Bucket'] == 'test-bucket'


def test_lambda_handler_uses_dynamodb_json_format(mock_dynamodb):
    from src.rack_designer.lambdas.export_handler import lambda_handler
    mock_dynamodb.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    lambda_handler({}, None)
    call_kwargs = mock_dynamodb.export_table_to_point_in_time.call_args[1]
    assert call_kwargs['ExportFormat'] == 'DYNAMODB_JSON'


def test_lambda_handler_returns_export_arn(mock_dynamodb):
    from src.rack_designer.lambdas.export_handler import lambda_handler
    expected_arn = 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
    mock_dynamodb.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': expected_arn
        }
    }
    result = lambda_handler({}, None)
    assert result['body']['export_arn'] == expected_arn


def test_lambda_handler_returns_s3_path(mock_dynamodb):
    from src.rack_designer.lambdas.export_handler import lambda_handler
    mock_dynamodb.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    result = lambda_handler({}, None)
    assert result['body']['s3_path'].startswith('s3://test-bucket/exports/events/')


def test_lambda_handler_returns_timestamp(mock_dynamodb):
    from src.rack_designer.lambdas.export_handler import lambda_handler
    mock_dynamodb.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    result = lambda_handler({}, None)
    assert 'timestamp' in result['body']
