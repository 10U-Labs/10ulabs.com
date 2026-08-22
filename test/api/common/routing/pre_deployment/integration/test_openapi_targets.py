"""Tests that every published route points at a Lambda some stack creates.

The API's routes live in openapi.json, and the functions that answer them are
created by Terraform in other directories. Nothing makes the two agree: the
spec names a template variable, apigateway.tf resolves it to a function name,
and a name no stack creates deploys just as happily as one that does. A route
wired that way returns nothing useful and says nothing about why, so the check
belongs here, where both halves can be read at once.
"""
import json
import re

import pytest

from repo_utils import REPO_ROOT
from terraform_config import extract_lambda_function_names, parse_lambda_handler_names

SRC_ROOT = REPO_ROOT / "src"
OPENAPI_PATH = SRC_ROOT / "www" / "api" / "openapi.json"
APIGATEWAY_PATH = SRC_ROOT / "api" / "common" / "routing" / "apigateway.tf"


def _integrated_paths() -> list:
    """List each route in openapi.json with the template variable it integrates."""
    spec = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
    found = []
    for route, operations in spec.get("paths", {}).items():
        for method, operation in operations.items():
            if not isinstance(operation, dict):
                continue
            integration = operation.get("x-amazon-apigateway-integration") or {}
            match = re.fullmatch(r"\$\{(\w+)\}", integration.get("uri", ""))
            if match:
                found.append((route, method, match.group(1)))
    return sorted(set(found))


def _template_variable_handlers() -> dict:
    """Map each templatefile variable in apigateway.tf to a handler name key.

    The spec is handed '${SessionsHandlerArn}', apigateway.tf assigns that from
    'local.sessions_arn', and that local interpolates
    'local.lambda_function_names.sessions', which is the handler key.
    """
    content = APIGATEWAY_PATH.read_text(encoding="utf-8")
    local_keys = dict(re.findall(
        r"^\s*(\w+)\s*=\s*\"[^\"]*local\.lambda_function_names\.(\w+)[^\"]*\"\s*$",
        content,
        re.MULTILINE,
    ))
    handler_keys = dict(re.findall(
        r"^\s*(\w+)\s*=\s*module\.common\.lambda_handler_names\.(\w+)\s*$",
        content,
        re.MULTILINE,
    ))
    variables = {}
    for variable, local_name in re.findall(
        r"^\s*(\w+)\s*=\s*local\.(\w+)\s*$", content, re.MULTILINE
    ):
        key = local_keys.get(local_name)
        if key is not None:
            variables[variable] = handler_keys.get(key, key)
    return variables


def _declared_function_names() -> set:
    """List every Lambda function name the Terraform under src/ creates."""
    declared = set()
    for path in SRC_ROOT.rglob("*.tf"):
        for _, function_name in extract_lambda_function_names(path, use_handler_names=True):
            declared.add(function_name)
    return declared


def _resolved_target(variable: str) -> str:
    """Resolve one openapi template variable to the function name it names."""
    key = _template_variable_handlers().get(variable)
    return parse_lambda_handler_names().get(key, "") if key else ""


INTEGRATED_PATHS = _integrated_paths()


@pytest.mark.parametrize(
    "route,method,variable",
    INTEGRATED_PATHS,
    ids=[f"{verb.upper()} {name}" for name, verb, _ in INTEGRATED_PATHS],
)
def test_route_integrates_a_declared_lambda(route: str, method: str, variable: str) -> None:
    """Test that this route's integration names a Lambda declared under src/."""
    target = _resolved_target(variable)
    assert target in _declared_function_names(), (
        f"{method.upper()} {route} integrates ${{{variable}}}, which resolves to "
        f"{target or 'no function name'}, and no .tf file under src/ declares an "
        f"aws_lambda_function with that name"
    )
