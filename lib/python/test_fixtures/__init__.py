"""Test fixtures package for shared pytest fixtures.

Re-exports commonly used terraform_config functions for convenience.
"""
from terraform_config import (
    get_shared_config,
    get_tfvars_values,
    get_endpoint_local_values,
)

__all__ = [
    'get_shared_config',
    'get_tfvars_values',
    'get_endpoint_local_values',
]
