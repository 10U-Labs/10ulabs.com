"""Utilities for working with Python modules in tests."""
from types import ModuleType
from typing import Any


def reset_module_state(module: ModuleType, **state_vars: Any) -> None:
    """Reset module-level state variables to specified values.

    This is useful for resetting cached state in Lambda handler modules
    between tests.

    Args:
        module: The module object to reset state on.
        **state_vars: Mapping of variable names to their reset values.

    Example:
        reset_module_state(handler_module,
            _clients={},
            _cache={'value': None},
            _dependencies_validated=False
        )
    """
    for var_name, default_value in state_vars.items():
        if hasattr(module, var_name):
            setattr(module, var_name, default_value)
