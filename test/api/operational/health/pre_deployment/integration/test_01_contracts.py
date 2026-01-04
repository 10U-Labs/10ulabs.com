"""Layer 1: Contract tests for health endpoint pre-deployment.

Tests that local files that must work together are compatible. No AWS calls.

Seven-layer testing model:
- Layer 1: Contracts - Local files are compatible
"""
import ast

import pytest
from repo_utils import REPO_ROOT



HEALTH_SRC = REPO_ROOT / "src" / "api" / "operational" / "health"


class TestLambdaHandlerContract:
    """Layer 1: Verify Lambda handler exports match Terraform references."""

    def test_handler_module_exports_handler_function(self):
        """Verify handler.py exports a function named 'handler'.

        lambda.tf references handler = "handler.handler" which means
        the handler.py module must export a function named 'handler'.
        """
        handler_path = HEALTH_SRC / "lambda" / "handler.py"
        handler_content = handler_path.read_text()

        tree = ast.parse(handler_content)
        function_names = [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]

        assert "handler" in function_names, (
            "handler.py must export a function named 'handler' "
            "(referenced by lambda.tf as handler = \"handler.handler\")"
        )

    def test_handler_function_accepts_event_and_context(self):
        """Verify handler function accepts event and context parameters.

        Lambda runtime calls handler(event, context), so the function
        must accept at least two positional parameters.
        """
        handler_path = HEALTH_SRC / "lambda" / "handler.py"
        handler_content = handler_path.read_text()

        tree = ast.parse(handler_content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "handler":
                param_count = len(node.args.args)
                assert param_count >= 2, (
                    f"handler function must accept at least 2 parameters "
                    f"(event, context), found {param_count}"
                )
                return

        pytest.fail("handler function not found in handler.py")
