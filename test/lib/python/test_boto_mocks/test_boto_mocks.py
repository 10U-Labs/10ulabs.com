from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from boto_mocks import (
    create_client_error,
    create_multi_client_mock,
    create_boto_client_mock,
    create_mock_lambda_list_mappings_error,
    create_mock_lambda_put_concurrency_error,
    create_mock_sns_publish_error,
    create_mock_lambda_with_mappings,
    create_mock_lambda_with_disabled_mappings,
    create_mock_lambda_delete_concurrency_error,
)


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


def test_returns_ec2_mock_for_ec2() -> None:
    ec2_mock = MagicMock()
    ssm_mock = MagicMock()
    client_mock = create_multi_client_mock(ec2_mock, ssm_mock)
    assert client_mock("ec2") is ec2_mock


def test_returns_ssm_mock_for_ssm() -> None:
    ec2_mock = MagicMock()
    ssm_mock = MagicMock()
    client_mock = create_multi_client_mock(ec2_mock, ssm_mock)
    assert client_mock("ssm") is ssm_mock


def test_returns_additional_mock_for_extra_service() -> None:
    ec2_mock = MagicMock()
    ssm_mock = MagicMock()
    sqs_mock = MagicMock()
    client_mock = create_multi_client_mock(ec2_mock, ssm_mock, sqs=sqs_mock)
    assert client_mock("sqs") is sqs_mock


def test_create_multi_client_mock_returns_magicmock_for_unknown_service() -> None:
    ec2_mock = MagicMock()
    ssm_mock = MagicMock()
    client_mock = create_multi_client_mock(ec2_mock, ssm_mock)
    result = client_mock("unknown")
    assert isinstance(result, MagicMock)


def test_returns_configured_mock_for_service() -> None:
    sqs_mock = MagicMock()
    client_mock = create_boto_client_mock(sqs=sqs_mock)
    assert client_mock("sqs") is sqs_mock


def test_create_boto_client_mock_returns_magicmock_for_unknown_service() -> None:
    client_mock = create_boto_client_mock()
    result = client_mock("unknown")
    assert isinstance(result, MagicMock)


def test_handles_multiple_services_ec2() -> None:
    ec2_mock = MagicMock()
    s3_mock = MagicMock()
    client_mock = create_boto_client_mock(ec2=ec2_mock, s3=s3_mock)
    assert client_mock("ec2") is ec2_mock


def test_handles_multiple_services_s3() -> None:
    ec2_mock = MagicMock()
    s3_mock = MagicMock()
    client_mock = create_boto_client_mock(ec2=ec2_mock, s3=s3_mock)
    assert client_mock("s3") is s3_mock


def test_create_mock_lambda_list_mappings_error_returns_magicmock() -> None:
    mock = create_mock_lambda_list_mappings_error()
    assert isinstance(mock, MagicMock)


def test_list_event_source_mappings_raises_client_error() -> None:
    mock = create_mock_lambda_list_mappings_error()
    raised = False
    try:
        mock.list_event_source_mappings()
    except ClientError:
        raised = True
    assert raised is True


def test_list_event_source_mappings_error_code() -> None:
    mock = create_mock_lambda_list_mappings_error()
    try:
        mock.list_event_source_mappings()
    except ClientError as e:
        assert e.response["Error"]["Code"] == "ServiceUnavailable"


def test_create_mock_lambda_put_concurrency_error_returns_magicmock() -> None:
    mock = create_mock_lambda_put_concurrency_error()
    assert isinstance(mock, MagicMock)


def test_put_function_concurrency_raises_client_error() -> None:
    mock = create_mock_lambda_put_concurrency_error()
    raised = False
    try:
        mock.put_function_concurrency()
    except ClientError:
        raised = True
    assert raised is True


def test_put_function_concurrency_error_code() -> None:
    mock = create_mock_lambda_put_concurrency_error()
    try:
        mock.put_function_concurrency()
    except ClientError as e:
        assert e.response["Error"]["Code"] == "ServiceUnavailable"


def test_create_mock_sns_publish_error_returns_magicmock() -> None:
    mock = create_mock_sns_publish_error()
    assert isinstance(mock, MagicMock)


def test_publish_raises_client_error() -> None:
    mock = create_mock_sns_publish_error()
    raised = False
    try:
        mock.publish()
    except ClientError:
        raised = True
    assert raised is True


def test_publish_error_code() -> None:
    mock = create_mock_sns_publish_error()
    try:
        mock.publish()
    except ClientError as e:
        assert e.response["Error"]["Code"] == "ServiceUnavailable"


def test_create_mock_lambda_with_mappings_returns_magicmock() -> None:
    mock = create_mock_lambda_with_mappings()
    assert isinstance(mock, MagicMock)


def test_list_event_source_mappings_returns_one_mapping() -> None:
    mock = create_mock_lambda_with_mappings()
    result = mock.list_event_source_mappings()
    assert len(result["EventSourceMappings"]) == 1


def test_list_event_source_mappings_returns_enabled_state() -> None:
    mock = create_mock_lambda_with_mappings()
    result = mock.list_event_source_mappings()
    assert result["EventSourceMappings"][0]["State"] == "Enabled"


def test_list_event_source_mappings_returns_uuid() -> None:
    mock = create_mock_lambda_with_mappings()
    result = mock.list_event_source_mappings()
    assert result["EventSourceMappings"][0]["UUID"] == "test-uuid"


def test_create_mock_lambda_with_disabled_mappings_returns_magicmock() -> None:
    mock = create_mock_lambda_with_disabled_mappings()
    assert isinstance(mock, MagicMock)


def test_list_event_source_mappings_returns_one_disabled_mapping() -> None:
    mock = create_mock_lambda_with_disabled_mappings()
    result = mock.list_event_source_mappings()
    assert len(result["EventSourceMappings"]) == 1


def test_list_event_source_mappings_returns_disabled_state() -> None:
    mock = create_mock_lambda_with_disabled_mappings()
    result = mock.list_event_source_mappings()
    assert result["EventSourceMappings"][0]["State"] == "Disabled"


def test_create_mock_lambda_delete_concurrency_error_returns_magicmock() -> None:
    mock = create_mock_lambda_delete_concurrency_error()
    assert isinstance(mock, MagicMock)


def test_delete_function_concurrency_raises_client_error() -> None:
    mock = create_mock_lambda_delete_concurrency_error()
    raised = False
    try:
        mock.delete_function_concurrency()
    except ClientError:
        raised = True
    assert raised is True


def test_delete_function_concurrency_error_code() -> None:
    mock = create_mock_lambda_delete_concurrency_error()
    try:
        mock.delete_function_concurrency()
    except ClientError as e:
        assert e.response["Error"]["Code"] == "ServiceUnavailable"
