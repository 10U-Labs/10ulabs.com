import json
from types import ModuleType
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

from lambda_clients import reset_clients
from test_fixtures.unit import create_client_error, create_mock_dynamodb_client


def test_generate_config_hash_returns_9_char_string(handler: ModuleType) -> None:
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result = handler.generate_config_hash(config)
    assert len(result) == 9


def test_generate_config_hash_uses_only_valid_chars(handler: ModuleType) -> None:
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result = handler.generate_config_hash(config)
    valid_chars = set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    assert all(c in valid_chars for c in result)


def test_generate_config_hash_same_config_same_hash(handler: ModuleType) -> None:
    config1 = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    config2 = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result1 = handler.generate_config_hash(config1)
    result2 = handler.generate_config_hash(config2)
    assert result1 == result2


def test_generate_config_hash_different_config_different_hash(handler: ModuleType) -> None:
    config1 = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    config2 = {'rackHeight': 24, 'rackCount': 3, 'placedParts': []}
    result1 = handler.generate_config_hash(config1)
    result2 = handler.generate_config_hash(config2)
    assert result1 != result2


def test_generate_config_hash_order_independent(handler: ModuleType) -> None:
    config1 = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    config2 = {'placedParts': [], 'rackCount': 3, 'rackHeight': 12}
    result1 = handler.generate_config_hash(config1)
    result2 = handler.generate_config_hash(config2)
    assert result1 == result2


def test_handle_get_missing_config_hash(handler: ModuleType) -> None:
    event: Dict[str, Any] = {'pathParameters': {}, 'headers': {}}
    response = handler.handle_get(event)
    assert response['statusCode'] == 400


def test_handle_get_invalid_config_hash_format(handler: ModuleType) -> None:
    event = {'pathParameters': {'config_hash': 'invalid'}, 'headers': {}}
    response = handler.handle_get(event)
    assert response['statusCode'] == 400


def _run_handle_get(
    mock_boto_client: MagicMock,
    handler: ModuleType,
    return_item: Any = None
) -> Any:
    mock_boto_client.return_value = create_mock_dynamodb_client('get_item', return_item)
    reset_clients()
    event = {'pathParameters': {'config_hash': 'ABCD12345'}, 'headers': {}}
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        return handler.handle_get(event)


@patch('boto3.client')
def test_handle_get_not_found(mock_boto_client: MagicMock, handler: ModuleType) -> None:
    response = _run_handle_get(mock_boto_client, handler)
    assert response['statusCode'] == 404


@patch('boto3.client')
def test_handle_get_success(mock_boto_client: MagicMock, handler: ModuleType) -> None:
    config_json = json.dumps({'rackHeight': 12, 'rackCount': 3, 'placedParts': []})
    item = {'Item': {'config_hash': {'S': 'ABCD12345'}, 'configuration': {'S': config_json}}}
    response = _run_handle_get(mock_boto_client, handler, item)
    assert response['statusCode'] == 200


def test_lambda_handler_options_returns_cors(handler: ModuleType) -> None:
    event = {'httpMethod': 'OPTIONS', 'path': '/v1/rack-configurations'}
    response = handler.lambda_handler(event, None)
    assert response['statusCode'] == 200


def test_lambda_handler_routes_get(handler: ModuleType) -> None:
    mock_return = {'statusCode': 200, 'body': '{}'}
    with patch.object(handler, 'handle_get', return_value=mock_return) as mock_handler:
        event = {
            'httpMethod': 'GET',
            'path': '/v1/rack-configurations/ABCD12345',
            'headers': {}
        }
        handler.lambda_handler(event, None)
        mock_handler.assert_called_once()
    assert True


def test_lambda_handler_unknown_path_returns_404(handler: ModuleType) -> None:
    event = {'httpMethod': 'GET', 'path': '/v1/unknown', 'headers': {}}
    response = handler.lambda_handler(event, None)
    assert response['statusCode'] == 404


def _create_load_mock_with_item(config_hash: str, config: Dict[str, Any]) -> MagicMock:
    mock_dynamodb = MagicMock()
    mock_dynamodb.get_item.return_value = {
        'Item': {
            'config_hash': {'S': config_hash},
            'configuration': {'S': json.dumps(config)}
        }
    }
    mock_dynamodb.put_item.return_value = {}
    mock_dynamodb.delete_item.return_value = {}
    return mock_dynamodb


def _run_load_configuration(
    mock_boto_client: MagicMock,
    handler: ModuleType,
    config_hash: str,
    mock_dynamodb: MagicMock
) -> Any:
    mock_boto_client.return_value = mock_dynamodb
    reset_clients()
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        return handler.load_rack_configuration(config_hash)


@patch('boto3.client')
def test_load_rack_configuration_returns_error_on_client_error(
    mock_boto_client: MagicMock,
    handler: ModuleType
) -> None:
    mock_dynamodb = MagicMock()
    mock_dynamodb.get_item.side_effect = create_client_error('InternalServerError', 'GetItem')
    result = _run_load_configuration(mock_boto_client, handler, 'ABCD12345', mock_dynamodb)
    assert result['success'] is False


@patch('boto3.client')
def test_load_rack_configuration_triggers_migration_for_8_char_hash(
    mock_boto_client: MagicMock, handler: ModuleType
) -> None:
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    mock_dynamodb = _create_load_mock_with_item('ABCD1234', config)
    result = _run_load_configuration(mock_boto_client, handler, 'ABCD1234', mock_dynamodb)
    assert len(result.get('config_hash', '')) == 9


@patch('boto3.client')
def test_load_rack_configuration_skips_migration_for_9_char_hash(
    mock_boto_client: MagicMock, handler: ModuleType
) -> None:
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    mock_dynamodb = _create_load_mock_with_item('ABCD12345', config)
    result = _run_load_configuration(mock_boto_client, handler, 'ABCD12345', mock_dynamodb)
    assert result == {'success': True, 'config_hash': 'ABCD12345', 'configuration': config}


def _run_migrate(
    mock_boto_client: MagicMock,
    handler: ModuleType,
    old_hash: str,
    config: Dict[str, Any],
    mock_dynamodb: Optional[MagicMock] = None
) -> Any:
    if mock_dynamodb is None:
        mock_dynamodb = MagicMock()
        mock_dynamodb.put_item.return_value = {}
        mock_dynamodb.delete_item.return_value = {}
    mock_boto_client.return_value = mock_dynamodb
    reset_clients()
    with patch.dict('os.environ', {'RACK_CONFIGURATIONS_TABLE': 'test-table'}):
        return handler.migrate_rack_configuration(old_hash, config)


@patch('boto3.client')
def test_migrate_rack_configuration_returns_none_when_hash_unchanged(
    mock_boto_client: MagicMock, handler: ModuleType
) -> None:
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    new_hash = handler.generate_config_hash(config)
    result = _run_migrate(mock_boto_client, handler, new_hash, config)
    assert result is None


@patch('boto3.client')
def test_migrate_rack_configuration_returns_new_hash_on_success(
    mock_boto_client: MagicMock, handler: ModuleType
) -> None:
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result = _run_migrate(mock_boto_client, handler, 'OLDHASH8', config)
    assert len(result) == 9


@patch('boto3.client')
def test_migrate_rack_configuration_returns_none_on_client_error(
    mock_boto_client: MagicMock, handler: ModuleType
) -> None:
    mock_dynamodb = MagicMock()
    mock_dynamodb.put_item.side_effect = create_client_error('InternalServerError', 'PutItem')
    config = {'rackHeight': 12, 'rackCount': 3, 'placedParts': []}
    result = _run_migrate(mock_boto_client, handler, 'OLDHASH8', config, mock_dynamodb)
    assert result is None


def test_error_response_includes_details_when_provided(handler: ModuleType) -> None:
    response = handler.error_response(500, 'Test error', 'Additional details')
    body = json.loads(response['body'])
    assert body['details'] == 'Additional details'


def test_error_response_omits_details_when_empty(handler: ModuleType) -> None:
    response = handler.error_response(400, 'Test error', '')
    body = json.loads(response['body'])
    assert 'details' not in body


def test_error_response_sets_correct_status_code(handler: ModuleType) -> None:
    response = handler.error_response(503, 'Service unavailable')
    assert response['statusCode'] == 503


def test_json_response_includes_cors_allow_origin(handler: ModuleType) -> None:
    response = handler.json_response(200, {'data': 'test'})
    assert response['headers']['Access-Control-Allow-Origin'] == '*'


def test_json_response_includes_cors_allow_methods(handler: ModuleType) -> None:
    response = handler.json_response(200, {'data': 'test'})
    assert 'GET' in response['headers']['Access-Control-Allow-Methods']


def test_json_response_sets_content_type_json(handler: ModuleType) -> None:
    response = handler.json_response(200, {'data': 'test'})
    assert response['headers']['Content-Type'] == 'application/json'


