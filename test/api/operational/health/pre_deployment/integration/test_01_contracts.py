import ast
import re

import pytest
from repo_utils import REPO_ROOT


HEALTH_SRC = REPO_ROOT / "src" / "api" / "operational" / "health"
HEALTH_WORKFLOW = (
    REPO_ROOT / ".github" / "workflows" / "api_operational_health.yml"
)


class TestLambdaHandlerContract:
    def test_handler_module_exports_handler_function(self) -> None:
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

    def test_handler_function_accepts_event_and_context(self) -> None:
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


def test_backend_state_key_matches_workflow_concurrency_group() -> None:
    backend_content = (HEALTH_SRC / "backend.tf").read_text()
    workflow_content = HEALTH_WORKFLOW.read_text()

    key_match = re.search(
        r'^\s*key\s*=\s*"([^"]+)"', backend_content, re.MULTILINE
    )
    group_match = re.search(
        r'^\s*group:\s*(\S+)', workflow_content, re.MULTILINE
    )
    state_key = key_match.group(1) if key_match else "<backend.tf declares no key>"
    group = (
        group_match.group(1) if group_match
        else "<api_operational_health.yml declares no concurrency group>"
    )

    assert state_key == group, (
        f"backend.tf key '{state_key}' and api_operational_health.yml concurrency "
        f"group '{group}' have drifted, so the lock protects a state file the "
        f"workflow is not writing"
    )
