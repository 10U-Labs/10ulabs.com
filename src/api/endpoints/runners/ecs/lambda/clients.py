"""AWS client management for ECS runner API.

Re-exports from shared aws_clients module for backwards compatibility.
"""
from aws_clients import (
    get_ec2_client,
    get_ecs_client,
    get_ecr_client,
    get_ssm_client,
    get_dynamodb_client,
    set_client,
    reset_clients,
)

__all__ = [
    'get_ec2_client',
    'get_ecs_client',
    'get_ecr_client',
    'get_ssm_client',
    'get_dynamodb_client',
    'set_client',
    'reset_clients',
]
