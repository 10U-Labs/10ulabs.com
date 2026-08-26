import ast

import pytest
from repo_utils import REPO_ROOT


HEALTH_SRC = REPO_ROOT / "src" / "api" / "operational" / "health"


class TestLambdaHandlerContract:
    def test_handler_module_exports_handler_function(self):
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

    def test_handler_function_accepts_event_and_context(self):
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
