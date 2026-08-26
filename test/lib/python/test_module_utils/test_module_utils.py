import sys
import tempfile
from pathlib import Path
from types import ModuleType

import pytest

from module_utils import (
    load_module_from_path,
    reset_module_state,
    create_lambda_loader,
)


class TestLoadModuleFromPath:
    def test_loads_module_from_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("VALUE = 42\n")
            f.flush()
            module = load_module_from_path("test_module", Path(f.name))
            assert module.VALUE == 42

    def test_returns_module_type(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("pass\n")
            f.flush()
            module = load_module_from_path("test_module", Path(f.name))
            assert isinstance(module, ModuleType)

    def test_module_has_correct_name(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("pass\n")
            f.flush()
            module = load_module_from_path("custom_name", Path(f.name))
            assert module.__name__ == "custom_name"

    def test_loads_module_with_functions(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("def add(a, b):\n    return a + b\n")
            f.flush()
            module = load_module_from_path("math_module", Path(f.name))
            assert module.add(2, 3) == 5


class TestResetModuleState:
    def test_resets_existing_attribute(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("counter = 10\n")
            f.flush()
            module = load_module_from_path("counter_module", Path(f.name))
            module.counter = 100
            reset_module_state(module, counter=0)
            assert module.counter == 0

    def test_ignores_nonexistent_attribute(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("value = 1\n")
            f.flush()
            module = load_module_from_path("simple_module", Path(f.name))
            reset_module_state(module, nonexistent=0)
            assert not hasattr(module, "nonexistent")

    @pytest.fixture
    def multi_attr_module_after_reset(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("a = 1\nb = 2\nc = 3\n")
            f.flush()
            module = load_module_from_path("multi_module", Path(f.name))
            module.a = 100
            module.b = 200
            reset_module_state(module, a=0, b=0)
            return module

    def test_resets_multiple_attributes_first(self, multi_attr_module_after_reset):
        assert multi_attr_module_after_reset.a == 0

    def test_resets_multiple_attributes_second(self, multi_attr_module_after_reset):
        assert multi_attr_module_after_reset.b == 0

    def test_resets_multiple_attributes_leaves_third(
        self, multi_attr_module_after_reset
    ):
        assert multi_attr_module_after_reset.c == 3

    def test_resets_dict_attribute(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("cache = {'key': 'value'}\n")
            f.flush()
            module = load_module_from_path("cache_module", Path(f.name))
            module.cache["new_key"] = "new_value"
            reset_module_state(module, cache={})
            assert module.cache == {}


class TestCreateLambdaLoader:
    def test_returns_callable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = create_lambda_loader(Path(tmpdir))
            assert callable(loader)

    def test_loader_loads_module(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            handler_path = Path(tmpdir) / "handler.py"
            handler_path.write_text("HANDLER_VALUE = 'loaded'\n")

            loader = create_lambda_loader(Path(tmpdir))
            module = loader("handler.py", "handler_module")
            assert module.HANDLER_VALUE == "loaded"

    def test_loader_adds_dir_to_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            handler_path = Path(tmpdir) / "handler.py"
            handler_path.write_text("pass\n")

            if tmpdir in sys.path:
                sys.path.remove(tmpdir)

            loader = create_lambda_loader(Path(tmpdir))
            loader("handler.py", "handler_module")
            assert tmpdir in sys.path

    def test_loader_does_not_duplicate_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            handler_path = Path(tmpdir) / "handler.py"
            handler_path.write_text("pass\n")

            sys.path.insert(0, tmpdir)
            initial_count = sys.path.count(tmpdir)

            loader = create_lambda_loader(Path(tmpdir))
            loader("handler.py", "handler_module")

            assert sys.path.count(tmpdir) == initial_count
