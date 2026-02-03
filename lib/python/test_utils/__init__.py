"""Shared test utilities for pytest test suites."""
import sys

from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT
from test_utils.aws_assertions import (
    assert_lambda_exists,
    assert_sqs_queue_exists,
)
from test_utils.terraform_assertions import (
    get_missing_terraform_files,
    lambda_handler_exists,
)


def create_endpoint_handler_loader(endpoint_path: str):
    """Create a handler module loader for a specific endpoint.

    Args:
        endpoint_path: Path relative to src/api/endpoints (e.g., 'sessions')

    Returns:
        A function that loads handler modules from the endpoint's lambda directory.
    """
    src_path = REPO_ROOT / "src" / "api" / "endpoints" / endpoint_path
    lambda_path = src_path / "lambda"

    if str(lambda_path) not in sys.path:
        sys.path.insert(0, str(lambda_path))

    return create_lambda_loader(lambda_path)


__all__ = [
    'assert_lambda_exists',
    'assert_sqs_queue_exists',
    'create_endpoint_handler_loader',
    'get_missing_terraform_files',
    'lambda_handler_exists',
]
