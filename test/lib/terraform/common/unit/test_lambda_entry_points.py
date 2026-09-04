import ast
import re
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT
from terraform_config import packaged_lambda_sources

SRC_ROOT = REPO_ROOT / "src"
ENTRY_POINT_NAME = "lambda_handler"
SETTING_PATTERN = re.compile(r'^\s*handler\s*=\s*"([^"]+)"', re.MULTILINE)


def _defines(source: Path, function_name: str) -> bool:
    tree = ast.parse(source.read_text(encoding="utf-8"))
    return any(
        isinstance(node, ast.FunctionDef) and node.name == function_name
        for node in ast.walk(tree)
    )


def _stack_files() -> list:
    return sorted(
        path for path in SRC_ROOT.rglob("*.tf") if ".terraform" not in path.parts
    )


CONFIGURED_ENTRY_POINTS = [
    ("src/api/common/routing/lambda.tf", "handler.lambda_handler"),
    ("src/api/endpoints/contact_submissions/lambda.tf", "handler.lambda_handler"),
    ("src/api/endpoints/rack_configurations/lambda.tf", "handler.lambda_handler"),
    ("src/api/endpoints/sessions/analytics.tf", "handler.lambda_handler"),
    ("src/api/endpoints/sessions/lambda.tf", "handler.lambda_handler"),
    ("src/api/operational/diagnostics/lambda.tf", "handler.lambda_handler"),
    ("src/api/operational/health/lambda.tf", "handler.lambda_handler"),
    ("src/www/common/lambda_edge.tf", "handler.lambda_handler"),
]

DEFINED_ENTRY_POINTS = [
    "src/api/common/routing/lambda/handler.py",
    "src/api/endpoints/contact_submissions/lambda/handler.py",
    "src/api/endpoints/rack_configurations/lambda/handler.py",
    "src/api/endpoints/sessions/lambda/exporter/handler.py",
    "src/api/endpoints/sessions/lambda/tracker/handler.py",
    "src/api/operational/diagnostics/lambda/handler.py",
    "src/api/operational/health/lambda/handler.py",
    "src/www/common/lambda/handler.py",
]


def _packages_entry_point(stack_file: Path, source: Path) -> bool:
    return any(
        (stack_file.parent / packaged).resolve() == source
        for packaged in packaged_lambda_sources(stack_file)
    ) and any(
        setting.rsplit(".", 1)[0] == source.stem
        for setting in SETTING_PATTERN.findall(stack_file.read_text(encoding="utf-8"))
    )


@pytest.mark.parametrize("tf_file, setting", CONFIGURED_ENTRY_POINTS)
def test_entry_point_carries_the_agreed_name(tf_file: str, setting: str) -> None:
    assert setting.rsplit(".", 1)[-1] == ENTRY_POINT_NAME, (
        f"{tf_file} is set to enter its function at {setting}, so it is "
        f"entered by a name the other deployed functions do not use; every "
        f"one of them is entered at {ENTRY_POINT_NAME}"
    )


@pytest.mark.parametrize("tf_file, setting", CONFIGURED_ENTRY_POINTS)
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


@pytest.mark.parametrize("source_file", DEFINED_ENTRY_POINTS)
def test_every_defined_entry_point_is_packaged_by_a_stack(source_file: str) -> None:
    source = (REPO_ROOT / source_file).resolve()
    assert any(
        _packages_entry_point(stack_file, source) for stack_file in _stack_files()
    ), (
        f"{source_file} defines {ENTRY_POINT_NAME}, but no .tf file under src "
        f"packages it under a handler setting naming {source.stem}, so it is "
        f"deployed nowhere and invoked by nothing; delete it, or restore the "
        f"stack that packaged it"
    )
