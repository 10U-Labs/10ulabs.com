"""Unit tests for aws_clients module."""
from unittest.mock import MagicMock, patch

import pytest

from .conftest import load_lambda_module


@pytest.fixture(name="aws_clients_module")
def aws_clients_module_fixture():
    """Load aws_clients module for testing."""
    with patch('boto3.client') as mock_boto_client:
        mock_boto_client.return_value = MagicMock()
        module = load_lambda_module("common/aws_clients.py", "aws_clients")
        # Clear the cache to ensure fresh state for each test
        module._cache = {
            "dynamodb_client": None,
            "ec2_client": None,
            "ecs_client": None,
            "s3_client": None,
            "sns_client": None,
            "sqs_client": None,
            "ssm_client": None,
        }
        yield module


class TestGetDynamodbClient:
    """Tests for get_dynamodb_client function."""

    def test_creates_client_on_first_call(self, aws_clients_module):
        """Test that client is created on first call."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            result = aws_clients_module.get_dynamodb_client()
            mock_boto.assert_called_once_with("dynamodb")
            assert result == mock_client

    def test_returns_cached_client_on_second_call(self, aws_clients_module):
        """Test that cached client is returned on subsequent calls."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            first_call = aws_clients_module.get_dynamodb_client()
            second_call = aws_clients_module.get_dynamodb_client()
            assert mock_boto.call_count == 1 and first_call is second_call


class TestGetEc2Client:
    """Tests for get_ec2_client function."""

    def test_creates_client_on_first_call(self, aws_clients_module):
        """Test that client is created on first call."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            result = aws_clients_module.get_ec2_client()
            mock_boto.assert_called_once_with("ec2")
            assert result == mock_client

    def test_returns_cached_client(self, aws_clients_module):
        """Test that cached client is returned."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            first_call = aws_clients_module.get_ec2_client()
            second_call = aws_clients_module.get_ec2_client()
            assert first_call is second_call


class TestGetEcsClient:
    """Tests for get_ecs_client function."""

    def test_creates_client_on_first_call(self, aws_clients_module):
        """Test that client is created on first call."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            result = aws_clients_module.get_ecs_client()
            mock_boto.assert_called_once_with("ecs")
            assert result == mock_client

    def test_returns_cached_client(self, aws_clients_module):
        """Test that cached client is returned."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            first_call = aws_clients_module.get_ecs_client()
            second_call = aws_clients_module.get_ecs_client()
            assert first_call is second_call


class TestGetS3Client:
    """Tests for get_s3_client function."""

    def test_creates_client_on_first_call(self, aws_clients_module):
        """Test that client is created on first call."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            result = aws_clients_module.get_s3_client()
            mock_boto.assert_called_once_with("s3")
            assert result == mock_client

    def test_returns_cached_client(self, aws_clients_module):
        """Test that cached client is returned."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            first_call = aws_clients_module.get_s3_client()
            second_call = aws_clients_module.get_s3_client()
            assert first_call is second_call


class TestGetSnsClient:
    """Tests for get_sns_client function."""

    def test_creates_client_on_first_call(self, aws_clients_module):
        """Test that client is created on first call."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            result = aws_clients_module.get_sns_client()
            mock_boto.assert_called_once_with("sns")
            assert result == mock_client

    def test_returns_cached_client(self, aws_clients_module):
        """Test that cached client is returned."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            first_call = aws_clients_module.get_sns_client()
            second_call = aws_clients_module.get_sns_client()
            assert first_call is second_call


class TestGetSqsClient:
    """Tests for get_sqs_client function."""

    def test_creates_client_on_first_call(self, aws_clients_module):
        """Test that client is created on first call."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            result = aws_clients_module.get_sqs_client()
            mock_boto.assert_called_once_with("sqs")
            assert result == mock_client

    def test_returns_cached_client(self, aws_clients_module):
        """Test that cached client is returned."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            first_call = aws_clients_module.get_sqs_client()
            second_call = aws_clients_module.get_sqs_client()
            assert first_call is second_call


class TestGetSsmClient:
    """Tests for get_ssm_client function."""

    def test_creates_client_on_first_call(self, aws_clients_module):
        """Test that client is created on first call."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            result = aws_clients_module.get_ssm_client()
            mock_boto.assert_called_once_with("ssm")
            assert result == mock_client

    def test_returns_cached_client(self, aws_clients_module):
        """Test that cached client is returned."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            first_call = aws_clients_module.get_ssm_client()
            second_call = aws_clients_module.get_ssm_client()
            assert first_call is second_call
