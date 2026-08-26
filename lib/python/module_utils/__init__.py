import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


def load_module_from_path(module_name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reset_module_state(module: ModuleType, **state_vars: Any) -> None:
    for var_name, default_value in state_vars.items():
        if hasattr(module, var_name):
            setattr(module, var_name, default_value)


def create_lambda_loader(lambdas_dir: Path):
    def load_lambda_module(filename: str, module_name: str) -> ModuleType:
        handler_path = lambdas_dir / filename
        lambdas_dir_str = str(lambdas_dir)
        if lambdas_dir_str not in sys.path:
            sys.path.insert(0, lambdas_dir_str)
        return load_module_from_path(module_name, handler_path)
    return load_lambda_module
