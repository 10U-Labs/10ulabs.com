"""Utilities for working with Python modules in tests."""
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


def load_module_from_path(module_name: str, path: Path) -> ModuleType:
    """Load a Python module from a file path.

    Args:
        module_name: Name to give the loaded module.
        path: Path to the Python file to load.

    Returns:
        The loaded module object.
    """
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def create_lambda_loader(lambdas_dir: Path):
    """Create a lambda loader function for a specific lambdas directory.

    Args:
        lambdas_dir: Path to the lambdas directory

    Returns:
        Function that loads lambda modules by filename
    """
    def load_lambda_module(filename: str, module_name: str) -> ModuleType:
        """Load a lambda module by filename."""
        handler_path = lambdas_dir / filename
        lambdas_dir_str = str(lambdas_dir)
        if lambdas_dir_str not in sys.path:
            sys.path.insert(0, lambdas_dir_str)
        return load_module_from_path(module_name, handler_path)
    return load_lambda_module
