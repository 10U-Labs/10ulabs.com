from unittest.mock import MagicMock, patch

from lambda_clients import get_dynamodb_client, reset_clients


def test_creates_a_client_when_not_cached() -> None:
    reset_clients()
    with patch('boto3.client') as mock_boto:
        get_dynamodb_client()
        assert mock_boto.call_args.args == ('dynamodb',)


def test_returns_the_created_client() -> None:
    reset_clients()
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        assert get_dynamodb_client() is mock_boto.return_value


def test_reuses_the_cached_client() -> None:
    reset_clients()
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = MagicMock()
        assert get_dynamodb_client() is get_dynamodb_client()


def test_creates_the_client_only_once() -> None:
    reset_clients()
    with patch('boto3.client') as mock_boto:
        get_dynamodb_client()
        get_dynamodb_client()
        assert mock_boto.call_count == 1


def test_reset_clients_forces_a_new_client() -> None:
    reset_clients()
    with patch('boto3.client') as mock_boto:
        get_dynamodb_client()
        reset_clients()
        get_dynamodb_client()
        assert mock_boto.call_count == 2
