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
    return sorted(
        (str(path.relative_to(REPO_ROOT)), setting)
        for path in SRC_ROOT.rglob("*.tf")
        if ".terraform" not in path.parts
        for setting in SETTING_PATTERN.findall(path.read_text(encoding="utf-8"))
    )


def _defines(source: Path, function_name: str) -> bool:
    tree = ast.parse(source.read_text(encoding="utf-8"))
    return any(
        isinstance(node, ast.FunctionDef) and node.name == function_name
        for node in ast.walk(tree)
    )


@pytest.mark.parametrize("tf_file, setting", _configured_entry_points())
def test_entry_point_carries_the_agreed_name(tf_file: str, setting: str) -> None:
    assert setting.rsplit(".", 1)[-1] == ENTRY_POINT_NAME, (
        f"{tf_file} is set to enter its function at {setting}, so it is "
        f"entered by a name the other deployed functions do not use; every "
        f"one of them is entered at {ENTRY_POINT_NAME}"
    )


@pytest.mark.parametrize("tf_file, setting", _configured_entry_points())
def test_entry_point_is_defined_by_the_code_it_names(
    tf_file: str, setting: str
) -> None:
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
