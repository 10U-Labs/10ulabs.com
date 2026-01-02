"""Lambda handler for rack designer API."""
import base64
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients: Dict[str, Any] = {}


def clear_clients() -> None:
    """Clear cached boto3 clients."""
    _clients.clear()


def get_dynamodb_client():
    """Get or create cached DynamoDB client."""
    if 'dynamodb' not in _clients:
        _clients['dynamodb'] = boto3.client('dynamodb')
    return _clients['dynamodb']


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Build a JSON API Gateway response with CORS headers."""
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(body)
    }
    return response


def error_response(status_code: int, message: str, details: str = '') -> Dict[str, Any]:
    """Build an error response with optional details."""
    body: Dict[str, Any] = {'success': False, 'error': message}
    if details:
        body['details'] = details
    response = json_response(status_code, body)
    return response


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse request body, handling base64 encoding if present."""
    body = event.get('body', '{}')
    if event.get('isBase64Encoded'):
        body = base64.b64decode(body).decode('utf-8')
    result = json.loads(body) if body else {}
    return result


def generate_config_hash(config: Dict[str, Any]) -> str:
    """Generate a 9-character hash from a rack configuration."""
    canonical = json.dumps(config, sort_keys=True, separators=(',', ':'))
    hash_bytes = hashlib.sha256(canonical.encode('utf-8')).digest()
    hash_int = int.from_bytes(hash_bytes[:6], 'big')
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    result_chars = []
    remaining = hash_int
    for _ in range(9):
        result_chars.append(chars[remaining % 36])
        remaining = remaining // 36
    config_hash = ''.join(result_chars)
    return config_hash


def save_rack_configuration(
    config_hash: str,
    config: Dict[str, Any],
    device_id: Optional[str] = None
) -> Dict[str, Any]:
    """Save a rack configuration to DynamoDB."""
    table_name = os.environ['RACK_DESIGNER_CONFIGURATIONS_TABLE']
    created_at = datetime.now(timezone.utc).isoformat()
    item: Dict[str, Any] = {
        'config_hash': {'S': config_hash},
        'configuration': {'S': json.dumps(config)},
        'created_at': {'S': created_at}
    }
    if device_id:
        item['device_id'] = {'S': device_id}
    try:
        get_dynamodb_client().put_item(
            TableName=table_name,
            Item=item,
            ConditionExpression='attribute_not_exists(config_hash)'
        )
        logger.info("Saved rack configuration: %s", config_hash)
        result = {'success': True, 'config_hash': config_hash}
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.info("Configuration already exists: %s", config_hash)
            result = {'success': True, 'config_hash': config_hash}
        else:
            logger.error("Error saving rack configuration: %s", e)
            result = {'success': False, 'error': str(e)}
    return result


def migrate_rack_configuration(old_hash: str, config: Dict[str, Any]) -> Optional[str]:
    """Migrate a rack configuration to a new hash if needed."""
    new_hash = generate_config_hash(config)
    if old_hash == new_hash:
        return None
    table_name = os.environ['RACK_DESIGNER_CONFIGURATIONS_TABLE']
    try:
        get_dynamodb_client().put_item(
            TableName=table_name,
            Item={
                'config_hash': {'S': new_hash},
                'configuration': {'S': json.dumps(config)}
            }
        )
        get_dynamodb_client().delete_item(
            TableName=table_name,
            Key={'config_hash': {'S': old_hash}}
        )
        logger.info("Migrated rack configuration: %s -> %s", old_hash, new_hash)
    except ClientError as e:
        logger.error("Error migrating rack configuration: %s", e)
        return None
    return new_hash


def load_rack_configuration(config_hash: str) -> Dict[str, Any]:
    """Load a rack configuration from DynamoDB by hash."""
    table_name = os.environ['RACK_DESIGNER_CONFIGURATIONS_TABLE']
    try:
        response = get_dynamodb_client().get_item(
            TableName=table_name,
            Key={'config_hash': {'S': config_hash}}
        )
        item = response.get('Item')
        if not item:
            result = {'success': False, 'error': 'Configuration not found'}
        else:
            config = json.loads(item['configuration']['S'])
            result_hash = config_hash
            if len(config_hash) == 8:
                new_hash = migrate_rack_configuration(config_hash, config)
                if new_hash:
                    result_hash = new_hash
            result = {'success': True, 'config_hash': result_hash, 'configuration': config}
    except ClientError as e:
        logger.error("Error loading rack configuration: %s", e)
        result = {'success': False, 'error': str(e)}
    return result


def validate_rack_configuration(config: Dict[str, Any]) -> Optional[str]:
    """Validate a rack configuration, returning error message if invalid."""
    error_msg = None
    if 'rackHeight' not in config:
        error_msg = 'Missing required field: rackHeight'
    elif 'rackCount' not in config:
        error_msg = 'Missing required field: rackCount'
    elif 'placedParts' not in config:
        error_msg = 'Missing required field: placedParts'
    elif not isinstance(config['rackHeight'], int):
        error_msg = 'rackHeight must be an integer'
    elif not isinstance(config['rackCount'], int):
        error_msg = 'rackCount must be an integer'
    elif not isinstance(config['placedParts'], list):
        error_msg = 'placedParts must be an array'
    elif config['rackHeight'] < 1 or config['rackHeight'] > 42:
        error_msg = 'rackHeight must be between 1 and 42'
    elif config['rackCount'] < 1:
        error_msg = 'rackCount must be at least 1'
    return error_msg


def handle_post(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST request to save a rack configuration."""
    try:
        body = parse_body(event)
        config = body.get('configuration')
        device_id = body.get('device_id')
        if not device_id:
            response = error_response(400, 'Missing required field: device_id')
        elif not config:
            response = error_response(400, 'Missing required field: configuration')
        else:
            validation_error = validate_rack_configuration(config)
            if validation_error:
                response = error_response(400, validation_error)
            else:
                config_hash = generate_config_hash(config)
                result = save_rack_configuration(config_hash, config, device_id)
                if result['success']:
                    response = json_response(200, {'success': True, 'config_hash': config_hash})
                else:
                    response = error_response(500, result['error'])
    except (ValueError, KeyError) as e:
        logger.error("Error handling rack designer POST: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


def handle_get(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET request to retrieve a rack configuration."""
    path_params = event.get('pathParameters') or {}
    config_hash = path_params.get('config_hash')
    if not config_hash:
        response = error_response(400, 'Missing required path parameter: config_hash')
    elif not re.match(r'^[0-9A-Z]{8,9}$', config_hash):
        response = error_response(400, 'Invalid config_hash format')
    else:
        result = load_rack_configuration(config_hash)
        if result['success']:
            response = json_response(200, result)
        else:
            response = error_response(404, result['error'])
    return response


def lambda_handler(event, _context):
    """Main Lambda handler for rack designer API requests."""
    logger.info("Received API request: %s", json.dumps(event))

    method = event.get('httpMethod', '')
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }

    path = event.get('path', '')

    if path == '/v1/rack-configurations' and method == 'POST':
        response = handle_post(event)
    elif path.startswith('/v1/rack-configurations/') and method == 'GET':
        response = handle_get(event)
    else:
        response = error_response(404, 'Not found')

    return response
