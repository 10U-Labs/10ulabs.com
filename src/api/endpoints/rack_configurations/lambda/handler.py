import hashlib
import json
import logging
import os
import re
from typing import Any, Dict, Optional
from botocore.exceptions import ClientError
from lambda_clients import get_dynamodb_client
from lambda_http import dispatch, error_response, json_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def generate_config_hash(config: Dict[str, Any]) -> str:
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


def migrate_rack_configuration(old_hash: str, config: Dict[str, Any]) -> Optional[str]:
    new_hash = generate_config_hash(config)
    if old_hash == new_hash:
        return None
    table_name = os.environ['RACK_CONFIGURATIONS_TABLE']
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
    table_name = os.environ['RACK_CONFIGURATIONS_TABLE']
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


def handle_get(event: Dict[str, Any]) -> Dict[str, Any]:
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


def _is_read(path: str, method: str) -> bool:
    return path.startswith('/v1/rack-configurations/') and method == 'GET'


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    logger.info("Received API request: %s", json.dumps(event))
    return dispatch(event, (
        (_is_read, handle_get),
    ))
