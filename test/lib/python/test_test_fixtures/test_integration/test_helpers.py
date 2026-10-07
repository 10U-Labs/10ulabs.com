from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from boto_mocks import create_client_error
from test_fixtures.integration.helpers import (
    aws_call_error,
    get_aws_account_id_via_cli,
    s3_head_bucket_problem,
)


@patch("test_fixtures.integration.helpers.subprocess.run")
def test_returns_account_id_on_success(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="123456789012\n")
    result = get_aws_account_id_via_cli()
    assert result == "123456789012"


@patch("test_fixtures.integration.helpers.subprocess.run")
def test_strips_whitespace_from_output(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="  123456789012  \n")
    result = get_aws_account_id_via_cli()
    assert result == "123456789012"


@patch("test_fixtures.integration.helpers.subprocess.run")
def test_calls_aws_command(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="123456789012")
    get_aws_account_id_via_cli()
    call_args = mock_run.call_args[0][0]
    assert "aws" in call_args


@patch("test_fixtures.integration.helpers.subprocess.run")
def test_calls_sts_service(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="123456789012")
    get_aws_account_id_via_cli()
    call_args = mock_run.call_args[0][0]
    assert "sts" in call_args


@patch("test_fixtures.integration.helpers.subprocess.run")
def test_calls_get_caller_identity_action(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="123456789012")
    get_aws_account_id_via_cli()
    call_args = mock_run.call_args[0][0]
    assert "get-caller-identity" in call_args


@patch("test_fixtures.integration.helpers.subprocess.run")
def test_get_aws_account_id_via_cli_failure(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=1, stdout="")
    result = get_aws_account_id_via_cli()
    assert result == ""


def test_no_problem_when_bucket_accessible() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.return_value = {}
    assert s3_head_bucket_problem(mock_client, "my-bucket") == ""


def test_calls_head_bucket_with_bucket_name() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.return_value = {}
    s3_head_bucket_problem(mock_client, "my-bucket")
    assert mock_client.head_bucket.call_args[1]["Bucket"] == "my-bucket"


def test_s3_head_bucket_problem_reports_403_error() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("403")
    assert s3_head_bucket_problem(mock_client, "my-bucket")


def test_reports_access_denied_error() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("AccessDenied")
    assert s3_head_bucket_problem(mock_client, "my-bucket")


def test_problem_contains_bucket_name() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("403")
    assert "my-bucket" in s3_head_bucket_problem(mock_client, "my-bucket")


def test_s3_head_bucket_problem_bucket_not_found() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("404")
    assert s3_head_bucket_problem(mock_client, "my-bucket") == ""


def test_s3_head_bucket_problem_other_errors() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("ServiceException")
    with pytest.raises(ClientError, match="ServiceException"):
        s3_head_bucket_problem(mock_client, "my-bucket")


def test_aws_call_error_empty_when_call_succeeds() -> None:
    mock_client = MagicMock()
    mock_client.list_buckets.return_value = {}
    assert aws_call_error(mock_client.list_buckets) == ""


def test_aws_call_error_names_the_error_code() -> None:
    mock_client = MagicMock()
    mock_client.list_buckets.side_effect = create_client_error("AccessDenied")
    assert "AccessDenied" in aws_call_error(mock_client.list_buckets)


def test_aws_call_error_carries_the_error_message() -> None:
    mock_client = MagicMock()
    mock_client.list_buckets.side_effect = create_client_error(
        "AccessDenied", message="no soup for you"
    )
    assert "no soup for you" in aws_call_error(mock_client.list_buckets)


def test_aws_call_error_empty_for_a_tolerated_code() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("404")
    assert aws_call_error(mock_client.head_bucket, "404") == ""


def test_aws_call_error_reports_an_untolerated_code() -> None:
    mock_client = MagicMock()
    mock_client.head_bucket.side_effect = create_client_error("403")
    assert aws_call_error(mock_client.head_bucket, "404")
