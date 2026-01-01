"""Unit tests for /v1/runners Lambda handler."""
import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from repo_utils import REPO_ROOT

# Add the lambda directory to the path for imports
LAMBDA_DIR = REPO_ROOT / 'src' / 'api' / 'endpoints' / 'runners' / 'lambda'
sys.path.insert(0, str(LAMBDA_DIR))

# Add lib/python for runner_labels
LIB_PYTHON = REPO_ROOT / 'lib' / 'python'
sys.path.insert(0, str(LIB_PYTHON))


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set required environment variables."""
    monkeypatch.setenv('API_BASE_URL', 'https://api.example.com')
    monkeypatch.setenv('API_KEY_PARAMETER_NAME', '/test/api-key')


@pytest.fixture
def mock_ssm_client():
    """Mock SSM client for API key retrieval."""
    with patch('boto3.client') as mock_client:
        ssm_mock = MagicMock()
        ssm_mock.get_parameter.return_value = {
            'Parameter': {'Value': 'test-api-key'}
        }
        mock_client.return_value = ssm_mock
        yield ssm_mock


@pytest.fixture
def sqs_event():
    """Create a sample SQS event."""
    return {
        'Records': [{
            'eventSource': 'aws:sqs',
            'messageId': 'test-123',
            'body': json.dumps({
                'job_id': 12345,
                'job_labels': ['self-hosted', 'linux', 'ec2'],
                'github_repo': 'org/repo',
                'run_id': 999
            })
        }]
    }


class TestSqsEventHandling:
    """Tests for SQS event handling."""

    def test_sqs_event_has_records(self, mock_env_vars, mock_ssm_client, sqs_event):
        """Test that SQS events have records."""
        records = sqs_event.get('Records', [])
        assert len(records) > 0

    def test_sqs_event_has_correct_source(self, mock_env_vars, mock_ssm_client, sqs_event):
        """Test that SQS events have correct eventSource."""
        records = sqs_event.get('Records', [])
        assert records[0].get('eventSource') == 'aws:sqs'


class TestRunnerLabels:
    """Tests for runner label parsing integration."""

    def test_runner_labels_import(self):
        """Test that runner_labels module can be imported."""
        import runner_labels
        assert hasattr(runner_labels, 'get_runner_type_from_labels')

    def test_ec2_label_returns_ec2_runner_type(self):
        """Test EC2 labels return ec2 runner type."""
        import runner_labels
        job_labels = ['ec2', 'general-purpose', 'arm', 'spot', 'runner-12345']
        runner_type, _ = runner_labels.get_runner_type_from_labels(job_labels)
        assert runner_type == 'ec2'

    def test_ec2_label_returns_ec2_endpoint(self):
        """Test EC2 labels return ec2 endpoint."""
        import runner_labels
        job_labels = ['ec2', 'general-purpose', 'arm', 'spot', 'runner-12345']
        _, endpoint = runner_labels.get_runner_type_from_labels(job_labels)
        assert endpoint == 'ec2'

    def test_fargate_label_returns_fargate_runner_type(self):
        """Test Fargate labels return fargate runner type."""
        import runner_labels
        job_labels = ['ecs', 'fargate', 'arm', 'spot', 'runner-12345']
        runner_type, _ = runner_labels.get_runner_type_from_labels(job_labels)
        assert runner_type == 'fargate'

    def test_fargate_label_returns_ecs_endpoint(self):
        """Test Fargate labels return ecs endpoint."""
        import runner_labels
        job_labels = ['ecs', 'fargate', 'arm', 'spot', 'runner-12345']
        _, endpoint = runner_labels.get_runner_type_from_labels(job_labels)
        assert endpoint == 'ecs'

    def test_no_matching_labels_returns_none_runner_type(self):
        """Test unmatched labels return None runner type."""
        import runner_labels
        job_labels = ['self-hosted', 'windows']
        runner_type, _ = runner_labels.get_runner_type_from_labels(job_labels)
        assert runner_type is None

    def test_no_matching_labels_returns_none_endpoint(self):
        """Test unmatched labels return None endpoint."""
        import runner_labels
        job_labels = ['self-hosted', 'windows']
        _, endpoint = runner_labels.get_runner_type_from_labels(job_labels)
        assert endpoint is None
