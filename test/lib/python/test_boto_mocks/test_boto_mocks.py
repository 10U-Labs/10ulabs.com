from botocore.exceptions import ClientError

from boto_mocks import create_client_error


def test_returns_client_error_instance() -> None:
    error = create_client_error("ResourceNotFoundException")
    assert isinstance(error, ClientError)


def test_sets_error_code() -> None:
    error = create_client_error("ResourceNotFoundException")
    assert error.response["Error"]["Code"] == "ResourceNotFoundException"


def test_sets_error_message() -> None:
    error = create_client_error("ResourceNotFoundException")
    assert "ResourceNotFoundException" in error.response["Error"]["Message"]


def test_sets_default_operation_name() -> None:
    error = create_client_error("ResourceNotFoundException")
    assert error.operation_name == "TestOperation"


def test_sets_custom_operation_name() -> None:
    error = create_client_error("ResourceNotFoundException", "GetItem")
    assert error.operation_name == "GetItem"


def test_sets_response_metadata_request_id() -> None:
    error = create_client_error("ResourceNotFoundException")
    assert "RequestId" in error.response["ResponseMetadata"]


def test_sets_response_metadata_status_code() -> None:
    error = create_client_error("ResourceNotFoundException")
    assert error.response["ResponseMetadata"]["HTTPStatusCode"] == 400
