import re
from pathlib import Path
from test.api.common.routing.conftest import _add_derived_config

import pytest

from repo_utils import REPO_ROOT

ROUTING_SRC = REPO_ROOT / "src" / "api" / "common" / "routing"
LAMBDA_DIR = ROUTING_SRC / "lambda"
UNIT_CONFTEST = (
    REPO_ROOT / "test" / "api" / "common" / "routing"
    / "pre_deployment" / "unit" / "conftest.py"
)
_DERIVED_NAME_PREFIX = "SentinelResourcePrefix"


def _extract_openapi_template_vars(openapi_path: Path) -> set[str]:
    content = openapi_path.read_text()
    pattern = r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}"
    return set(re.findall(pattern, content))


def _extract_templatefile_vars(apigateway_path: Path) -> set[str]:
    content = apigateway_path.read_text()

    match = re.search(
        r"templatefile\s*\(\s*\"[^\"]+\"\s*,\s*\{([^}]+)\}\s*\)",
        content,
        re.DOTALL,
    )
    if not match:
        return set()

    vars_block = match.group(1)
    var_pattern = r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*="
    return set(re.findall(var_pattern, vars_block, re.MULTILINE))


def test_openapi_json_exists(openapi_path: Path):
    assert openapi_path.exists(), f"openapi.json not found at {openapi_path}"


def test_apigateway_tf_exists(apigateway_path: Path):
    assert apigateway_path.exists(), f"apigateway.tf not found at {apigateway_path}"


def test_openapi_template_vars_all_provided(openapi_path: Path, apigateway_path: Path):
    if not openapi_path.exists() or not apigateway_path.exists():
        pytest.skip("Required files do not exist")

    openapi_vars = _extract_openapi_template_vars(openapi_path)
    templatefile_vars = _extract_templatefile_vars(apigateway_path)

    missing_vars = openapi_vars - templatefile_vars
    assert not missing_vars, (
        f"Template variables in openapi.json are missing from templatefile() call:\n"
        f"  Missing: {sorted(missing_vars)}\n"
        f"  openapi.json requires: {sorted(openapi_vars)}\n"
        f"  apigateway.tf provides: {sorted(templatefile_vars)}"
    )


def test_templatefile_vars_all_used(openapi_path: Path, apigateway_path: Path):
    if not openapi_path.exists() or not apigateway_path.exists():
        pytest.skip("Required files do not exist")

    openapi_vars = _extract_openapi_template_vars(openapi_path)
    templatefile_vars = _extract_templatefile_vars(apigateway_path)

    unused_vars = templatefile_vars - openapi_vars
    assert not unused_vars, (
        f"Variables passed to templatefile() are not used in openapi.json:\n"
        f"  Unused: {sorted(unused_vars)}\n"
        f"  apigateway.tf provides: {sorted(templatefile_vars)}\n"
        f"  openapi.json uses: {sorted(openapi_vars)}"
    )


def _extract_lambda_handlers_from_tf(lambda_tf_path: Path) -> list[tuple[str, str]]:
    content = lambda_tf_path.read_text()
    handlers = []

    resource_pattern = r'resource\s+"aws_lambda_function"\s+"(\w+)"'
    handler_pattern = r'handler\s*=\s*"([^"]+)"'

    for resource_match in re.finditer(resource_pattern, content):
        resource_name = resource_match.group(1)
        start = resource_match.end()
        next_resource = re.search(r'\nresource\s+', content[start:])
        end = start + next_resource.start() if next_resource else len(content)
        block_content = content[start:end]

        handler_match = re.search(handler_pattern, block_content)
        if handler_match:
            handler_ref = handler_match.group(1)
            handlers.append((resource_name, handler_ref))

    return handlers


def _extract_function_names_from_py(py_path: Path) -> set[str]:
    content = py_path.read_text()
    pattern = r'^def\s+(\w+)\s*\('
    return set(re.findall(pattern, content, re.MULTILINE))


def test_lambda_handler_exports_match_terraform_references(
    lambda_tf_path: Path, lambda_dir: Path
):
    if not lambda_tf_path.exists():
        pytest.skip("lambda.tf not found")

    handlers = _extract_lambda_handlers_from_tf(lambda_tf_path)
    if not handlers:
        pytest.skip("No Lambda handler references found in lambda.tf")

    errors = []
    for resource_name, handler_ref in handlers:
        parts = handler_ref.split(".")
        if len(parts) != 2:
            errors.append(
                f"  {resource_name}: Invalid handler format '{handler_ref}' "
                f"(expected 'filename.function_name')"
            )
            continue

        expected_module, expected_function = parts
        py_file = lambda_dir / f"{expected_module}.py"

        if not py_file.exists():
            errors.append(
                f"  {resource_name}: Handler references '{expected_module}.py' "
                f"but file does not exist at {py_file}"
            )
            continue

        functions = _extract_function_names_from_py(py_file)
        if expected_function not in functions:
            errors.append(
                f"  {resource_name}: Handler references function '{expected_function}' "
                f"but {expected_module}.py only exports: {sorted(functions)}"
            )

    assert not errors, (
        "Lambda handler contracts violated:\n" + "\n".join(errors)
    )


def _lambda_sources_the_unit_setup_opens() -> list[str]:
    content = UNIT_CONFTEST.read_text()
    return sorted(set(re.findall(r'load_lambda_module\(\s*"([^"]+)"', content)))


@pytest.mark.parametrize("lambda_source", _lambda_sources_the_unit_setup_opens())
def test_unit_setup_opens_a_lambda_source_that_exists(lambda_source: str):
    assert (LAMBDA_DIR / lambda_source).exists(), (
        f"The unit tier's setup opens '{lambda_source}', which is not in "
        f"{LAMBDA_DIR}. A test requesting that fixture dies with "
        f"FileNotFoundError."
    )


def _derived_resource_names() -> list[str]:
    derived: dict[str, str] = {"resource_prefix": _DERIVED_NAME_PREFIX}
    _add_derived_config(derived)
    return sorted(
        value.removeprefix(_DERIVED_NAME_PREFIX)
        for key, value in derived.items()
        if key != "resource_prefix"
    )


@pytest.mark.parametrize("derived_name", _derived_resource_names())
def test_derived_resource_name_is_built_by_this_terraform(derived_name: str):
    terraform = "\n".join(path.read_text() for path in sorted(ROUTING_SRC.glob("*.tf")))
    assert derived_name in terraform, (
        f"The shared setup derives a name ending '{derived_name}', which no "
        f"Terraform file in {ROUTING_SRC} builds. Whatever owned it has left."
    )
