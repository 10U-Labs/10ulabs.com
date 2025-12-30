"""Comprehensive tests for module_utils module."""
import sys
import tempfile
from pathlib import Path
from types import ModuleType

from module_utils import (
    load_module_from_path,
    reset_module_state,
    create_lambda_loader,
)


# === load_module_from_path ===


class TestLoadModuleFromPath:
    """Tests for load_module_from_path function."""

    def test_loads_module_from_file(self):
        """load_module_from_path loads a module from a file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("VALUE = 42\n")
            f.flush()
            module = load_module_from_path("test_module", Path(f.name))
            assert module.VALUE == 42

    def test_returns_module_type(self):
        """load_module_from_path returns a ModuleType."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("pass\n")
            f.flush()
            module = load_module_from_path("test_module", Path(f.name))
            assert isinstance(module, ModuleType)

    def test_module_has_correct_name(self):
        """load_module_from_path sets the module name."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("pass\n")
            f.flush()
            module = load_module_from_path("custom_name", Path(f.name))
            assert module.__name__ == "custom_name"

    def test_loads_module_with_functions(self):
        """load_module_from_path loads module with functions."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("def add(a, b):\n    return a + b\n")
            f.flush()
            module = load_module_from_path("math_module", Path(f.name))
            assert module.add(2, 3) == 5


# === reset_module_state ===


class TestResetModuleState:
    """Tests for reset_module_state function."""

    def test_resets_existing_attribute(self):
        """reset_module_state resets existing attributes."""
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
        """reset_module_state ignores nonexistent attributes."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("value = 1\n")
            f.flush()
            module = load_module_from_path("simple_module", Path(f.name))
            # Should not raise
            reset_module_state(module, nonexistent=0)
            assert not hasattr(module, "nonexistent")

    def test_resets_multiple_attributes_first(self):
        """reset_module_state resets first attribute."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("a = 1\nb = 2\nc = 3\n")
            f.flush()
            module = load_module_from_path("multi_module", Path(f.name))
            module.a = 100
            module.b = 200
            reset_module_state(module, a=0, b=0)
            assert module.a == 0

    def test_resets_multiple_attributes_second(self):
        """reset_module_state resets second attribute."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("a = 1\nb = 2\nc = 3\n")
            f.flush()
            module = load_module_from_path("multi_module", Path(f.name))
            module.a = 100
            module.b = 200
            reset_module_state(module, a=0, b=0)
            assert module.b == 0

    def test_resets_multiple_attributes_leaves_third(self):
        """reset_module_state leaves unreset attribute unchanged."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("a = 1\nb = 2\nc = 3\n")
            f.flush()
            module = load_module_from_path("multi_module", Path(f.name))
            module.a = 100
            module.b = 200
            reset_module_state(module, a=0, b=0)
            assert module.c == 3

    def test_resets_dict_attribute(self):
        """reset_module_state can reset dict attributes."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("cache = {'key': 'value'}\n")
            f.flush()
            module = load_module_from_path("cache_module", Path(f.name))
            module.cache["new_key"] = "new_value"
            reset_module_state(module, cache={})
            assert module.cache == {}


# === create_lambda_loader ===


class TestCreateLambdaLoader:
    """Tests for create_lambda_loader function."""

    def test_returns_callable(self):
        """create_lambda_loader returns a callable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = create_lambda_loader(Path(tmpdir))
            assert callable(loader)

    def test_loader_loads_module(self):
        """The returned loader loads a module from the directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handler_path = Path(tmpdir) / "handler.py"
            handler_path.write_text("HANDLER_VALUE = 'loaded'\n")

            loader = create_lambda_loader(Path(tmpdir))
            module = loader("handler.py", "handler_module")
            assert module.HANDLER_VALUE == "loaded"

    def test_loader_adds_dir_to_path(self):
        """The loader adds the lambdas directory to sys.path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handler_path = Path(tmpdir) / "handler.py"
            handler_path.write_text("pass\n")

            # Ensure it's not already in path
            if tmpdir in sys.path:
                sys.path.remove(tmpdir)

            loader = create_lambda_loader(Path(tmpdir))
            loader("handler.py", "handler_module")
            assert tmpdir in sys.path

    def test_loader_does_not_duplicate_path(self):
        """The loader does not add directory to path if already present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handler_path = Path(tmpdir) / "handler.py"
            handler_path.write_text("pass\n")

            # Pre-add to path
            sys.path.insert(0, tmpdir)
            initial_count = sys.path.count(tmpdir)

            loader = create_lambda_loader(Path(tmpdir))
            loader("handler.py", "handler_module")

            assert sys.path.count(tmpdir) == initial_count
