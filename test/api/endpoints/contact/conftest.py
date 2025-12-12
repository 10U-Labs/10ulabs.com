"""Pytest fixtures for contact endpoint tests."""
from pathlib import Path
from typing import Dict

import pytest

from terraform_config import (
    extract_iam_role_names,
    extract_lambda_function_names,
)

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
CONTACT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "contact"


@pytest.fixture(name="config", scope="module")
def config_fixture(shared_config) -> Dict[str, str]:
    """Create configuration fixture from shared config."""
    result: Dict[str, str] = {}
    result['aws_region'] = shared_config.get('aws_region', 'us-east-2')
    result['api_fqdn'] = f"api.{shared_config.get('domain_name', '')}"
    result['domain_name'] = shared_config.get('domain_name', '')
    return result


@pytest.fixture(scope="session")
def lambda_role_name():
    """Get the Lambda execution role name from Terraform source."""
    roles = extract_iam_role_names(CONTACT_SRC / "iam.tf")
    return roles[0][1] if roles else ""


@pytest.fixture(scope="session")
def lambda_function_name():
    """Get the Lambda function name from Terraform source."""
    functions = extract_lambda_function_names(CONTACT_SRC / "lambda.tf", use_handler_names=True)
    return functions[0][1] if functions else ""
