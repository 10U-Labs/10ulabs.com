from typing import Any, Dict

import boto3


_clients: Dict[str, Any] = {}


def get_dynamodb_client() -> Any:
    if 'dynamodb' not in _clients:
        _clients['dynamodb'] = boto3.client('dynamodb')
    return _clients['dynamodb']


def reset_clients() -> None:
    _clients.clear()
