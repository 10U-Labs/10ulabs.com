"""Shared fixtures for drift recoveries unit tests."""
import sys
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from module_utils import create_lambda_loader
from repo_utils import REPO_ROOT


DRIFT_RECOVERIES_SRC_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "drift_recoveries"
)
DRIFT_RECOVERIES_LAMBDA_PATH = DRIFT_RECOVERIES_SRC_PATH / "lambda"
TERRAFORM_DIR = DRIFT_RECOVERIES_SRC_PATH

# Add lambda path to sys.path so modules can be found when patching
if str(DRIFT_RECOVERIES_LAMBDA_PATH) not in sys.path:
    sys.path.insert(0, str(DRIFT_RECOVERIES_LAMBDA_PATH))

# Use shared lambda loader for drift recoveries lambda
load_lambda_module = create_lambda_loader(DRIFT_RECOVERIES_LAMBDA_PATH)


@pytest.fixture
def env_vars():
    """Mock environment variables for Lambda handler."""
    return {
        'GITHUB_REPO': '10U-Labs-LLC/10ulabs.com',
        'GITHUB_TOKEN_PARAMETER_NAME': '/10ULabs/GitHubToken',
        'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-2:123456789012:10ULabsAlerts',
        'MANAGED_VPC_ID': 'vpc-12345678',
    }


@pytest.fixture
def handler_module(request):
    """Provide the handler module with mocked environment."""
    env = request.getfixturevalue('env_vars')
    with patch.dict('os.environ', env):
        module = load_lambda_module("handler.py", "handler")
        yield module


@pytest.fixture
def sample_sqs_event() -> Dict[str, Any]:
    """Provide a sample SQS event with Config compliance change."""
    return {
        'Records': [{
            'messageId': 'test-message-id',
            'body': '''{
                "source": "drift-recovery-trigger",
                "configRuleName": "10ULabs-required-tags",
                "resourceType": "AWS::EC2::SecurityGroup",
                "resourceId": "sg-12345678",
                "awsRegion": "us-east-2"
            }'''
        }]
    }


@pytest.fixture
def sample_direct_event() -> Dict[str, Any]:
    """Provide a sample direct event (no SQS wrapper)."""
    return {
        'source': 'drift-recovery-trigger',
        'configRuleName': '10ULabs-required-tags',
        'resourceType': 'AWS::EC2::Subnet',
        'resourceId': 'subnet-12345678',
        'awsRegion': 'us-east-2',
    }


@pytest.fixture
def mock_ec2_client():
    """Provide a mock EC2 client."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_ssm_client():
    """Provide a mock SSM client."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_sns_client():
    """Provide a mock SNS client."""
    client = MagicMock()
    return client


# === Terraform file content fixtures ===


@pytest.fixture(name="terraform_dir")
def fixture_terraform_dir():
    """Provide path to drift_recoveries Terraform directory."""
    return TERRAFORM_DIR


@pytest.fixture(name="lambda_tf_content")
def fixture_lambda_tf_content(terraform_dir):
    """Provide lambda.tf file content."""
    return (terraform_dir / "lambda.tf").read_text()


@pytest.fixture(name="iam_tf_content")
def fixture_iam_tf_content(terraform_dir):
    """Provide iam.tf file content."""
    return (terraform_dir / "iam.tf").read_text()


@pytest.fixture(name="sqs_tf_content")
def fixture_sqs_tf_content(terraform_dir):
    """Provide sqs.tf file content."""
    return (terraform_dir / "sqs.tf").read_text()


@pytest.fixture(name="sns_tf_content")
def fixture_sns_tf_content(terraform_dir):
    """Provide sns.tf file content."""
    return (terraform_dir / "sns.tf").read_text()


@pytest.fixture(name="eventbridge_tf_content")
def fixture_eventbridge_tf_content(terraform_dir):
    """Provide eventbridge.tf file content."""
    return (terraform_dir / "eventbridge.tf").read_text()


@pytest.fixture(name="config_tf_content")
def fixture_config_tf_content(terraform_dir):
    """Provide config.tf file content."""
    return (terraform_dir / "config.tf").read_text()


@pytest.fixture(name="locals_tf_content")
def fixture_locals_tf_content(terraform_dir):
    """Provide locals.tf file content."""
    return (terraform_dir / "locals.tf").read_text()


@pytest.fixture(name="outputs_tf_content")
def fixture_outputs_tf_content(terraform_dir):
    """Provide outputs.tf file content."""
    return (terraform_dir / "outputs.tf").read_text()
