"""Comprehensive tests for aws_clients module."""
from unittest.mock import MagicMock, patch

import aws_clients
from aws_clients import (
    get_client,
    get_ec2_client,
    get_ssm_client,
    get_dynamodb_client,
    get_ecs_client,
    get_ecr_client,
    set_client,
    reset_clients,
)


class TestGetClient:
    """Tests for get_client function."""

    def setup_method(self):
        """Reset client cache before each test."""
        reset_clients()

    def teardown_method(self):
        """Reset client cache after each test."""
        reset_clients()

    @patch("aws_clients.boto3")
    def test_creates_new_client_calls_boto3(self, mock_boto3):
        """get_client calls boto3.client with service name."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        get_client("s3")
        mock_boto3.client.assert_called_once_with("s3")

    @patch("aws_clients.boto3")
    def test_creates_new_client_returns_client(self, mock_boto3):
        """get_client returns the boto3 client."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        result = get_client("s3")
        assert result is mock_client

    @patch("aws_clients.boto3")
    def test_returns_cached_client_same_instance(self, mock_boto3):
        """get_client returns same instance on subsequent calls."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        result1 = get_client("s3")
        result2 = get_client("s3")
        assert result1 is result2

    @patch("aws_clients.boto3")
    def test_returns_cached_client_only_one_call(self, mock_boto3):
        """get_client only calls boto3.client once for cached service."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        get_client("s3")
        get_client("s3")
        assert mock_boto3.client.call_count == 1

    @patch("aws_clients.boto3")
    def test_different_services_get_different_clients(self, mock_boto3):
        """get_client creates different clients for different services."""
        mock_s3 = MagicMock()
        mock_ec2 = MagicMock()
        mock_boto3.client.side_effect = [mock_s3, mock_ec2]
        result1 = get_client("s3")
        result2 = get_client("ec2")
        assert result1 is not result2

    @patch("aws_clients.boto3")
    def test_different_services_calls_boto3_twice(self, mock_boto3):
        """get_client calls boto3.client for each unique service."""
        mock_s3 = MagicMock()
        mock_ec2 = MagicMock()
        mock_boto3.client.side_effect = [mock_s3, mock_ec2]
        get_client("s3")
        get_client("ec2")
        assert mock_boto3.client.call_count == 2


class TestGetEc2Client:
    """Tests for get_ec2_client function."""

    def setup_method(self):
        """Reset client cache before each test."""
        reset_clients()

    def teardown_method(self):
        """Reset client cache after each test."""
        reset_clients()

    @patch("aws_clients.boto3")
    def test_returns_ec2_client_calls_boto3(self, mock_boto3):
        """get_ec2_client calls boto3 with ec2 service."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        get_ec2_client()
        mock_boto3.client.assert_called_with("ec2")

    @patch("aws_clients.boto3")
    def test_returns_ec2_client_returns_client(self, mock_boto3):
        """get_ec2_client returns the client."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        result = get_ec2_client()
        assert result is mock_client


class TestGetSsmClient:
    """Tests for get_ssm_client function."""

    def setup_method(self):
        """Reset client cache before each test."""
        reset_clients()

    def teardown_method(self):
        """Reset client cache after each test."""
        reset_clients()

    @patch("aws_clients.boto3")
    def test_returns_ssm_client_calls_boto3(self, mock_boto3):
        """get_ssm_client calls boto3 with ssm service."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        get_ssm_client()
        mock_boto3.client.assert_called_with("ssm")

    @patch("aws_clients.boto3")
    def test_returns_ssm_client_returns_client(self, mock_boto3):
        """get_ssm_client returns the client."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        result = get_ssm_client()
        assert result is mock_client


class TestGetDynamodbClient:
    """Tests for get_dynamodb_client function."""

    def setup_method(self):
        """Reset client cache before each test."""
        reset_clients()

    def teardown_method(self):
        """Reset client cache after each test."""
        reset_clients()

    @patch("aws_clients.boto3")
    def test_returns_dynamodb_client_calls_boto3(self, mock_boto3):
        """get_dynamodb_client calls boto3 with dynamodb service."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        get_dynamodb_client()
        mock_boto3.client.assert_called_with("dynamodb")

    @patch("aws_clients.boto3")
    def test_returns_dynamodb_client_returns_client(self, mock_boto3):
        """get_dynamodb_client returns the client."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        result = get_dynamodb_client()
        assert result is mock_client


class TestGetEcsClient:
    """Tests for get_ecs_client function."""

    def setup_method(self):
        """Reset client cache before each test."""
        reset_clients()

    def teardown_method(self):
        """Reset client cache after each test."""
        reset_clients()

    @patch("aws_clients.boto3")
    def test_returns_ecs_client_calls_boto3(self, mock_boto3):
        """get_ecs_client calls boto3 with ecs service."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        get_ecs_client()
        mock_boto3.client.assert_called_with("ecs")

    @patch("aws_clients.boto3")
    def test_returns_ecs_client_returns_client(self, mock_boto3):
        """get_ecs_client returns the client."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        result = get_ecs_client()
        assert result is mock_client


class TestGetEcrClient:
    """Tests for get_ecr_client function."""

    def setup_method(self):
        """Reset client cache before each test."""
        reset_clients()

    def teardown_method(self):
        """Reset client cache after each test."""
        reset_clients()

    @patch("aws_clients.boto3")
    def test_returns_ecr_client_calls_boto3(self, mock_boto3):
        """get_ecr_client calls boto3 with ecr service."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        get_ecr_client()
        mock_boto3.client.assert_called_with("ecr")

    @patch("aws_clients.boto3")
    def test_returns_ecr_client_returns_client(self, mock_boto3):
        """get_ecr_client returns the client."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        result = get_ecr_client()
        assert result is mock_client


class TestSetClient:
    """Tests for set_client function."""

    def setup_method(self):
        """Reset client cache before each test."""
        reset_clients()

    def teardown_method(self):
        """Reset client cache after each test."""
        reset_clients()

    def test_sets_client_in_cache(self):
        """set_client adds client to cache."""
        mock_client = MagicMock()
        set_client("custom", mock_client)
        assert aws_clients._clients["custom"] is mock_client

    def test_get_client_returns_set_client(self):
        """get_client returns client set by set_client."""
        mock_client = MagicMock()
        set_client("test", mock_client)
        result = get_client("test")
        assert result is mock_client


class TestResetClients:
    """Tests for reset_clients function."""

    def test_clears_client_cache(self):
        """reset_clients clears all cached clients."""
        set_client("test1", MagicMock())
        set_client("test2", MagicMock())
        reset_clients()
        assert len(aws_clients._clients) == 0

    @patch("aws_clients.boto3")
    def test_reset_allows_new_client_creation(self, mock_boto3):
        """After reset, get_client creates new client instead of returning cached."""
        mock_client1 = MagicMock(name="client1")
        mock_client2 = MagicMock(name="client2")
        mock_boto3.client.side_effect = [mock_client1, mock_client2]

        result1 = get_client("s3")
        reset_clients()
        result2 = get_client("s3")

        assert result1 is not result2
