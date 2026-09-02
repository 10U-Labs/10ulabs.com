import re
from pathlib import Path
from typing import Optional

import pytest


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
ENDPOINT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "contact_submissions"
LAMBDA_DIR = ENDPOINT_SRC / "lambda"


def _get_terraform_handler() -> Optional[str]:
    lambda_tf_path = ENDPOINT_SRC / "lambda.tf"
    content = lambda_tf_path.read_text()
    match = re.search(r'handler\s*=\s*"([^"]+)"', content)
    return match.group(1) if match else None


def test_lambda_handler_function_exists() -> None:
    handler_path = LAMBDA_DIR / "handler.py"
    content = handler_path.read_text()
    has_handler = "def lambda_handler(" in content
    assert has_handler


def test_terraform_lambda_tf_has_handler_config() -> None:
    terraform_handler = _get_terraform_handler()
    handler_is_configured = terraform_handler is not None
    assert handler_is_configured


def test_terraform_handler_has_correct_format() -> None:
    terraform_handler = _get_terraform_handler()
    parts = terraform_handler.split(".") if terraform_handler else []
    handler_has_two_parts = len(parts) == 2
    assert handler_has_two_parts


def test_terraform_handler_file_exists() -> None:
    terraform_handler = _get_terraform_handler()
    parts = terraform_handler.split(".") if terraform_handler else []
    handler_file = parts[0] if len(parts) == 2 else None
    handler_py_path = LAMBDA_DIR / f"{handler_file}.py" if handler_file else None
    handler_file_exists = handler_py_path.exists() if handler_py_path else False
    assert handler_file_exists


def test_terraform_handler_function_exists_in_file() -> None:
    terraform_handler = _get_terraform_handler()
    parts = terraform_handler.split(".") if terraform_handler else []
    if len(parts) != 2:
        pytest.skip("Handler format invalid")
    handler_file, handler_function = parts
    handler_py_path = LAMBDA_DIR / f"{handler_file}.py"
    handler_content = handler_py_path.read_text()
    function_pattern = rf"def {handler_function}\s*\("
    function_exists = re.search(function_pattern, handler_content) is not None
    assert function_exists


def test_lambda_directory_exists() -> None:
    lambda_dir_exists = LAMBDA_DIR.exists()
    assert lambda_dir_exists


@pytest.mark.parametrize("tf_file", ["lambda.tf", "iam.tf", "variables.tf"])
def test_terraform_file_exists(tf_file: str) -> None:
    tf_path = ENDPOINT_SRC / tf_file
    file_exists = tf_path.exists()
    assert file_exists
