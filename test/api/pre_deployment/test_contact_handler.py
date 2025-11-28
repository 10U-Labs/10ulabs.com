import json
from unittest.mock import patch, MagicMock, Mock
from test.api.pre_deployment.conftest import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
)


def create_contact_event(
    name="John Doe",
    email="john@example.com",
    message="Hello, this is a test message.",
    recaptcha_token="valid-token",
):
    body = {}
    if name is not None:
        body["name"] = name
    if email is not None:
        body["email"] = email
    if message is not None:
        body["message"] = message
    if recaptcha_token is not None:
        body["recaptcha_token"] = recaptcha_token
    return {
        "httpMethod": "POST",
        "path": "/v1/contact",
        "headers": {},
        "body": json.dumps(body),
        "requestContext": {"requestId": "test-id"},
    }


def test_handle_contact_post_with_valid_data_returns_200(v1_handler, lambda_context):
    with patch.object(v1_handler, "get_recaptcha_secret", return_value="secret"):
        with patch.object(v1_handler, "verify_recaptcha", return_value=True):
            with patch.object(v1_handler, "send_contact_email", return_value=True):
                with patch.dict("os.environ", {"CONTACT_EMAIL": "contact@test.com"}):
                    event = create_contact_event()
                    response = v1_handler.lambda_handler(event, lambda_context)
                    assert_response_status(response, 200)


def test_handle_contact_post_returns_json_content_type(v1_handler, lambda_context):
    with patch.object(v1_handler, "get_recaptcha_secret", return_value="secret"):
        with patch.object(v1_handler, "verify_recaptcha", return_value=True):
            with patch.object(v1_handler, "send_contact_email", return_value=True):
                with patch.dict("os.environ", {"CONTACT_EMAIL": "contact@test.com"}):
                    event = create_contact_event()
                    response = v1_handler.lambda_handler(event, lambda_context)
                    assert_json_content_type(response)


def test_handle_contact_post_with_valid_data_returns_success_true(v1_handler, lambda_context):
    with patch.object(v1_handler, "get_recaptcha_secret", return_value="secret"):
        with patch.object(v1_handler, "verify_recaptcha", return_value=True):
            with patch.object(v1_handler, "send_contact_email", return_value=True):
                with patch.dict("os.environ", {"CONTACT_EMAIL": "contact@test.com"}):
                    event = create_contact_event()
                    response = v1_handler.lambda_handler(event, lambda_context)
                    body = parse_response_body(response)
                    assert body["success"] is True


def test_handle_contact_post_with_missing_recaptcha_token_returns_400(v1_handler, lambda_context):
    event = create_contact_event(recaptcha_token="")
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_handle_contact_post_with_missing_name_returns_400(v1_handler, lambda_context):
    event = create_contact_event(name="")
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_handle_contact_post_with_name_too_long_returns_400(v1_handler, lambda_context):
    event = create_contact_event(name="x" * 101)
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_handle_contact_post_with_missing_email_returns_400(v1_handler, lambda_context):
    event = create_contact_event(email="")
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_handle_contact_post_with_email_too_long_returns_400(v1_handler, lambda_context):
    event = create_contact_event(email="x" * 256)
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_handle_contact_post_with_invalid_email_returns_400(v1_handler, lambda_context):
    event = create_contact_event(email="not-an-email")
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_handle_contact_post_with_missing_message_returns_400(v1_handler, lambda_context):
    event = create_contact_event(message="")
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_handle_contact_post_with_message_too_long_returns_400(v1_handler, lambda_context):
    event = create_contact_event(message="x" * 1001)
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 400)


def test_handle_contact_post_with_failed_recaptcha_returns_400(v1_handler, lambda_context):
    with patch.object(v1_handler, "get_recaptcha_secret", return_value="secret"):
        with patch.object(v1_handler, "verify_recaptcha", return_value=False):
            with patch.dict("os.environ", {"CONTACT_EMAIL": "contact@test.com"}):
                event = create_contact_event()
                response = v1_handler.lambda_handler(event, lambda_context)
                assert_response_status(response, 400)


def test_handle_contact_post_with_missing_recaptcha_secret_returns_500(v1_handler, lambda_context):
    with patch.object(v1_handler, "get_recaptcha_secret", return_value=""):
        with patch.dict("os.environ", {"CONTACT_EMAIL": "contact@test.com"}):
            event = create_contact_event()
            response = v1_handler.lambda_handler(event, lambda_context)
            assert_response_status(response, 500)


def test_handle_contact_post_with_missing_contact_email_returns_500(v1_handler, lambda_context):
    with patch.object(v1_handler, "get_recaptcha_secret", return_value="secret"):
        with patch.object(v1_handler, "verify_recaptcha", return_value=True):
            with patch.dict("os.environ", {"CONTACT_EMAIL": ""}):
                event = create_contact_event()
                response = v1_handler.lambda_handler(event, lambda_context)
                assert_response_status(response, 500)


def test_handle_contact_post_with_email_send_failure_returns_500(v1_handler, lambda_context):
    with patch.object(v1_handler, "get_recaptcha_secret", return_value="secret"):
        with patch.object(v1_handler, "verify_recaptcha", return_value=True):
            with patch.object(v1_handler, "send_contact_email", return_value=False):
                with patch.dict("os.environ", {"CONTACT_EMAIL": "contact@test.com"}):
                    event = create_contact_event()
                    response = v1_handler.lambda_handler(event, lambda_context)
                    assert_response_status(response, 500)


def test_handle_contact_post_with_invalid_json_returns_500(v1_handler, lambda_context):
    event = {
        "httpMethod": "POST",
        "path": "/v1/contact",
        "headers": {},
        "body": "not valid json",
        "requestContext": {"requestId": "test-id"},
    }
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 500)


def test_handle_contact_post_in_test_mode_returns_200(v1_handler, lambda_context):
    event = create_contact_event()
    event["headers"] = {"x-test-mode": "true"}
    response = v1_handler.lambda_handler(event, lambda_context)
    assert_response_status(response, 200)


def test_handle_contact_post_in_test_mode_returns_test_mode_true(v1_handler, lambda_context):
    event = create_contact_event()
    event["headers"] = {"x-test-mode": "true"}
    response = v1_handler.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    assert body["test_mode"] is True


def test_validate_contact_email_with_valid_email_returns_true(v1_handler):
    result = v1_handler.validate_contact_email("test@example.com")
    assert result is True


def test_validate_contact_email_with_invalid_email_returns_false(v1_handler):
    result = v1_handler.validate_contact_email("not-an-email")
    assert result is False


def test_validate_contact_email_with_empty_string_returns_false(v1_handler):
    result = v1_handler.validate_contact_email("")
    assert result is False


def test_verify_recaptcha_with_empty_token_returns_false(v1_handler):
    result = v1_handler.verify_recaptcha("", "secret")
    assert result is False


def test_verify_recaptcha_with_empty_secret_returns_false(v1_handler):
    result = v1_handler.verify_recaptcha("token", "")
    assert result is False


def test_get_ses_client_returns_client(v1_handler):
    with patch("boto3.client") as mock_boto:
        mock_ses = MagicMock()
        mock_boto.return_value = mock_ses
        v1_handler._clients.clear()
        client = v1_handler.get_ses_client()
        assert client is not None


def test_send_contact_email_calls_ses_send_email(v1_handler):
    mock_ses = MagicMock()
    v1_handler._clients["ses"] = mock_ses
    v1_handler.send_contact_email("to@test.com", "John", "from@test.com", "Hello")
    mock_ses.send_email.assert_called_once()


def test_send_contact_email_returns_true_on_success(v1_handler):
    mock_ses = MagicMock()
    v1_handler._clients["ses"] = mock_ses
    result = v1_handler.send_contact_email("to@test.com", "John", "from@test.com", "Hello")
    assert result is True


def test_send_contact_email_returns_false_on_client_error(v1_handler):
    from botocore.exceptions import ClientError
    mock_ses = MagicMock()
    mock_ses.send_email.side_effect = ClientError(
        {"Error": {"Code": "MessageRejected", "Message": "Test error"}},
        "SendEmail"
    )
    v1_handler._clients["ses"] = mock_ses
    result = v1_handler.send_contact_email("to@test.com", "John", "from@test.com", "Hello")
    assert result is False
