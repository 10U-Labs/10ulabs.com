import ast

import pytest
from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import (
    create_routing_wait_contract_tests,
    create_single_start_contract_tests,
    create_state_lock_contract_tests,
)


HEALTH_SRC = REPO_ROOT / "src" / "api" / "operational" / "health"

test_group_names_the_state_file = create_state_lock_contract_tests(
    HEALTH_SRC, "api_operational_health.yml"
)

TestRoutingWaitContract = create_routing_wait_contract_tests(
    "api_operational_health.yml"
)

TestSingleStartContract = create_single_start_contract_tests(
    "api_operational_health.yml"
)


def test_handler_module_exports_handler_function() -> None:
    handler_path = HEALTH_SRC / "lambda" / "handler.py"
    handler_content = handler_path.read_text()

    tree = ast.parse(handler_content)
    function_names = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    ]

    assert "lambda_handler" in function_names, (
        "handler.py must export a function named 'lambda_handler' "
        "(referenced by lambda.tf as handler = \"handler.lambda_handler\")"
    )


def test_handler_function_accepts_event_and_context() -> None:
    handler_path = HEALTH_SRC / "lambda" / "handler.py"
    handler_content = handler_path.read_text()

    tree = ast.parse(handler_content)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "lambda_handler":
            param_count = len(node.args.args)
            assert param_count >= 2, (
                f"lambda_handler function must accept at least 2 parameters "
                f"(event, context), found {param_count}"
            )
            return

    pytest.fail("lambda_handler function not found in handler.py")
