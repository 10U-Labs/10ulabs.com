import importlib.util
from pathlib import Path
from types import ModuleType


def load_lambda_module(filename: str, module_name: str) -> ModuleType:
    handler_path = Path(__file__).parent.parent.parent / "src" / "rack_designer" / "lambdas" / filename
    spec = importlib.util.spec_from_file_location(module_name, handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
