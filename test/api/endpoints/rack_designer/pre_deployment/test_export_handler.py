"""Unit tests for DynamoDB export handler."""


def test_lambda_handler_returns_status_code_200(export_module):
    """Test lambda handler returns 200 status code."""
    module, dynamodb_client = export_module
    dynamodb_client.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    result = module.lambda_handler({}, None)
    assert result['statusCode'] == 200


def test_lambda_handler_calls_export_table_to_point_in_time(export_module):
    """Test lambda handler calls export API."""
    module, dynamodb_client = export_module
    dynamodb_client.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    module.lambda_handler({}, None)
    assert dynamodb_client.export_table_to_point_in_time.called


def test_lambda_handler_uses_correct_table_arn(export_module):
    """Test lambda handler uses correct table ARN."""
    module, dynamodb_client = export_module
    dynamodb_client.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    module.lambda_handler({}, None)
    call_kwargs = dynamodb_client.export_table_to_point_in_time.call_args[1]
    expected = 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events'
    assert call_kwargs['TableArn'] == expected


def test_lambda_handler_uses_correct_s3_bucket(export_module):
    """Test lambda handler uses correct S3 bucket."""
    module, dynamodb_client = export_module
    dynamodb_client.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    module.lambda_handler({}, None)
    call_kwargs = dynamodb_client.export_table_to_point_in_time.call_args[1]
    assert call_kwargs['S3Bucket'] == 'test-bucket'


def test_lambda_handler_uses_dynamodb_json_format(export_module):
    """Test lambda handler uses DynamoDB JSON format."""
    module, dynamodb_client = export_module
    dynamodb_client.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    module.lambda_handler({}, None)
    call_kwargs = dynamodb_client.export_table_to_point_in_time.call_args[1]
    assert call_kwargs['ExportFormat'] == 'DYNAMODB_JSON'


def test_lambda_handler_returns_export_arn(export_module):
    """Test lambda handler returns export ARN."""
    module, dynamodb_client = export_module
    expected_arn = 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
    dynamodb_client.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': expected_arn
        }
    }
    result = module.lambda_handler({}, None)
    assert result['body']['export_arn'] == expected_arn


def test_lambda_handler_returns_s3_path(export_module):
    """Test lambda handler returns S3 path."""
    module, dynamodb_client = export_module
    dynamodb_client.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    result = module.lambda_handler({}, None)
    assert result['body']['s3_path'].startswith('s3://test-bucket/exports/events/')


def test_lambda_handler_returns_timestamp(export_module):
    """Test lambda handler returns timestamp."""
    module, dynamodb_client = export_module
    dynamodb_client.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    result = module.lambda_handler({}, None)
    assert 'timestamp' in result['body']


def test_lambda_handler_uses_correct_s3_prefix(export_module):
    """Test lambda handler uses correct S3 prefix."""
    module, dynamodb_client = export_module
    dynamodb_client.export_table_to_point_in_time.return_value = {
        'ExportDescription': {
            'ExportArn': 'arn:aws:dynamodb:us-east-1:123456789012:table/test-events/export/123'
        }
    }
    module.lambda_handler({}, None)
    call_kwargs = dynamodb_client.export_table_to_point_in_time.call_args[1]
    assert call_kwargs['S3Prefix'].startswith('exports/events/')
