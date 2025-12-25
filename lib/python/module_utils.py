"""Utilities for resetting and managing module state in tests.

Provides functions for resetting Lambda handler module caches and state
to ensure clean test isolation.
"""
from types import ModuleType


def reset_module_state(module: ModuleType) -> None:
    """Reset common cached state in a Lambda handler module.

    Clears cached clients, tokens, and validation states that handlers
    typically maintain for performance. This ensures test isolation.

    Args:
        module: The Lambda handler module to reset
    """
    # Clear client caches
    if hasattr(module, '_clients'):
        setattr(module, '_clients', {})

    # Clear token caches
    if hasattr(module, '_github_token_cache'):
        setattr(module, '_github_token_cache', {'value': None})
    if hasattr(module, '_api_key_cache'):
        setattr(module, '_api_key_cache', {'value': None})

    # Clear dependency validation cache
    if hasattr(module, '_dependencies_validated'):
        setattr(module, '_dependencies_validated', {
            'checked': True, 'valid': True, 'errors': []
        })
