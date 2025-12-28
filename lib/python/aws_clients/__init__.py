"""AWS client management for Lambda handlers."""
from typing import Any, Dict

import boto3

_clients: Dict[str, Any] = {}


def get_client(service_name: str) -> Any:
    """Get or create a cached boto3 client."""
    if service_name not in _clients:
        _clients[service_name] = boto3.client(service_name)
    return _clients[service_name]


def get_ec2_client():
    """Get or create a cached EC2 client."""
    return get_client('ec2')


def get_ssm_client():
    """Get or create a cached SSM client."""
    return get_client('ssm')


def get_dynamodb_client():
    """Get or create a cached DynamoDB client."""
    return get_client('dynamodb')


def get_ecs_client():
    """Get or create a cached ECS client."""
    return get_client('ecs')


def get_ecr_client():
    """Get or create a cached ECR client."""
    return get_client('ecr')


def set_client(name: str, client: Any):
    """Set a client in the cache for testing purposes."""
    _clients[name] = client


def reset_clients():
    """Clear all cached clients for testing purposes."""
    _clients.clear()
