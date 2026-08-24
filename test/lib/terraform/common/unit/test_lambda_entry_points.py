"""Tests that every deployed function is entered by the same name.

A deployment setting names the function the runtime calls when a request
arrives, and that name is written twice: once in the setting and once in the
code that gets packaged. Every other test of it reads one subsystem, compares
it against a value written down beside it, and so confirms only that the
subsystem agrees with itself. A subsystem that spells the name differently
from its neighbours is invisible to all of them, and the difference then reads
as though something about that function differs, which costs the next person
the time it takes to establish that nothing does.
"""
import ast
import re
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT
from terraform_config import packaged_lambda_sources

SRC_ROOT = REPO_ROOT / "src"
ENTRY_POINT_NAME = "lambda_handler"
SETTING_PATTERN = re.compile(r'^\s*handler\s*=\s*"([^"]+)"', re.MULTILINE)


def _configured_entry_points() -> list:
    """List the entry point each deployment setting under src/ names."""
    return sorted(
        (str(path.relative_to(REPO_ROOT)), setting)
        for path in SRC_ROOT.rglob("*.tf")
        if ".terraform" not in path.parts
        for setting in SETTING_PATTERN.findall(path.read_text(encoding="utf-8"))
    )


def _defines(source: Path, function_name: str) -> bool:
    """Report whether one Python file defines a function by this name."""
    tree = ast.parse(source.read_text(encoding="utf-8"))
    return any(
        isinstance(node, ast.FunctionDef) and node.name == function_name
        for node in ast.walk(tree)
    )


@pytest.mark.parametrize("tf_file, setting", _configured_entry_points())
def test_entry_point_carries_the_agreed_name(tf_file: str, setting: str) -> None:
    """Test that this deployment setting names the agreed entry point."""
    assert setting.rsplit(".", 1)[-1] == ENTRY_POINT_NAME, (
        f"{tf_file} is set to enter its function at {setting}, so it is "
        f"entered by a name the other deployed functions do not use; every "
        f"one of them is entered at {ENTRY_POINT_NAME}"
    )


@pytest.mark.parametrize("tf_file, setting", _configured_entry_points())
def test_entry_point_is_defined_by_the_code_it_names(
    tf_file: str, setting: str
) -> None:
    """Test that the code this setting points at defines the entry point."""
    module_name, function_name = setting.rsplit(".", 1)
    stack = (REPO_ROOT / tf_file).parent
    assert any(
        _defines(stack / packaged, function_name)
        for packaged in packaged_lambda_sources(REPO_ROOT / tf_file)
        if Path(packaged).name == f"{module_name}.py"
    ), (
        f"{tf_file} is set to enter its function at {setting}, but nothing it "
        f"packages is a {module_name}.py defining {function_name}, so the "
        f"deployed function has no entry point and answers nothing"
    )
