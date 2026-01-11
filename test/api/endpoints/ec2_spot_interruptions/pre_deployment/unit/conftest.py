"""Shared fixtures for EC2 spot interruptions pre-deployment unit tests."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT


ENDPOINT_NAME = "ec2_spot_interruptions"
EC2_SPOT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / ENDPOINT_NAME
EC2_SPOT_LAMBDA = EC2_SPOT_SRC / "lambda"

if str(EC2_SPOT_LAMBDA) not in sys.path:
    sys.path.insert(0, str(EC2_SPOT_LAMBDA))

load_lambda_module = create_lambda_loader(EC2_SPOT_LAMBDA)


@pytest.fixture
def ec2_spot_src_path() -> Path:
    """Provide path to ec2_spot_interruptions source directory."""
    return EC2_SPOT_SRC


@pytest.fixture
def handler_module(request):
    """Load the EC2 spot interruptions handler with mocked environment."""
    config = request.getfixturevalue('cfg')
    with patch.dict('os.environ', {
        'AWS_REGION': config['aws_region'],
        'RETRIES_QUEUE_URL': 'https://sqs.us-east-2.amazonaws.com/123456789012/test-queue',
    }):
        yield load_lambda_module("handler.py", "handler")
