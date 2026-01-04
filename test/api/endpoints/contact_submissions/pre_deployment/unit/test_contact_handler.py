"""Unit tests for contact form Lambda handler."""
import json
from unittest.mock import patch, MagicMock
from lambda_response import (
    parse_response_body,
    assert_response_status,
    assert_json_content_type,
)

from botocore.exceptions import ClientError


def create_contact_event(
    name="John Doe",
    email="john@example.com",
    message="Hello, this is a test message.",
    recaptcha_token="valid-token",
):
    """Create a contact form API Gateway event for testing."""
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
        "path": "/v1/contact-submissions",
        "headers": {},
        "body": json.dumps(body),
        "requestContext": {"requestId": "test-id"},
    }


def test_handle_contact_post_with_valid_data_returns_200(successful_contact_response):
    """Test that valid contact form submission returns 200."""
    assert successful_contact_response['statusCode'] == 200


def test_handle_contact_post_returns_json_content_type(successful_contact_response):
    """Test that contact POST response has JSON content type."""
    assert successful_contact_response['headers']['Content-Type'].startswith('application/json')


def test_handle_contact_post_with_valid_data_returns_success_true(successful_contact_response):
    """Test that valid contact form returns success true in body."""
    body = parse_response_body(successful_contact_response)
    success_is_true = body["success"] is True
    assert success_is_true


def test_handle_contact_post_with_missing_recaptcha_token_returns_400(
    contact_handler, lambda_context
):
    """Test that missing recaptcha token returns 400."""
    event = create_contact_event(recaptcha_token="")
    response = contact_handler.handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_missing_name_returns_400(contact_handler, lambda_context):
    """Test that missing name returns 400."""
    event = create_contact_event(name="")
    response = contact_handler.handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_name_too_long_returns_400(contact_handler, lambda_context):
    """Test that name over 100 characters returns 400."""
    event = create_contact_event(name="x" * 101)
    response = contact_handler.handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_missing_email_returns_400(contact_handler, lambda_context):
    """Test that missing email returns 400."""
    event = create_contact_event(email="")
    response = contact_handler.handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_email_too_long_returns_400(contact_handler, lambda_context):
    """Test that email over 255 characters returns 400."""
    event = create_contact_event(email="x" * 256)
    response = contact_handler.handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_invalid_email_returns_400(contact_handler, lambda_context):
    """Test that invalid email format returns 400."""
    event = create_contact_event(email="not-an-email")
    response = contact_handler.handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_missing_message_returns_400(contact_handler, lambda_context):
    """Test that missing message returns 400."""
    event = create_contact_event(message="")
    response = contact_handler.handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_message_too_long_returns_400(contact_handler, lambda_context):
    """Test that message over 1000 characters returns 400."""
    event = create_contact_event(message="x" * 1001)
    response = contact_handler.handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_failed_recaptcha_returns_400(contact_handler, lambda_context):
    """Test that failed reCAPTCHA verification returns 400."""
    with patch.object(contact_handler, "get_recaptcha_secret", return_value="secret"):
        with patch.object(contact_handler, "verify_recaptcha", return_value=False):
            with patch.dict("os.environ", {"CONTACT_EMAIL": "contact@test.com"}):
                event = create_contact_event()
                response = contact_handler.handler(event, lambda_context)
                assert response['statusCode'] == 400


def test_handle_contact_post_with_missing_recaptcha_secret_returns_500(
    contact_handler, lambda_context
):
    """Test that missing reCAPTCHA secret returns 500."""
    with patch.object(contact_handler, "get_recaptcha_secret", return_value=""):
        with patch.dict("os.environ", {"CONTACT_EMAIL": "contact@test.com"}):
            event = create_contact_event()
            response = contact_handler.handler(event, lambda_context)
            assert response['statusCode'] == 500


def test_handle_contact_post_with_missing_contact_email_returns_500(
    contact_handler, lambda_context
):
    """Test that missing contact email config returns 500."""
    with patch.object(contact_handler, "get_recaptcha_secret", return_value="secret"):
        with patch.object(contact_handler, "verify_recaptcha", return_value=True):
            with patch.dict("os.environ", {"CONTACT_EMAIL": ""}):
                event = create_contact_event()
                response = contact_handler.handler(event, lambda_context)
                assert response['statusCode'] == 500


def test_handle_contact_post_with_email_send_failure_returns_500(
    contact_handler, lambda_context
):
    """Test that email send failure returns 500."""
    with patch.object(contact_handler, "get_recaptcha_secret", return_value="secret"):
        with patch.object(contact_handler, "verify_recaptcha", return_value=True):
            with patch.object(contact_handler, "send_contact_email", return_value=False):
                with patch.dict("os.environ", {"CONTACT_EMAIL": "contact@test.com"}):
                    event = create_contact_event()
                    response = contact_handler.handler(event, lambda_context)
                    assert response['statusCode'] == 500


def test_handle_contact_post_with_invalid_json_returns_500(contact_handler, lambda_context):
    """Test that invalid JSON body returns 500."""
    event = {
        "httpMethod": "POST",
        "path": "/v1/contact-submissions",
        "headers": {},
        "body": "not valid json",
        "requestContext": {"requestId": "test-id"},
    }
    response = contact_handler.handler(event, lambda_context)
    assert response['statusCode'] == 500


def test_handle_contact_post_in_test_mode_returns_200(contact_handler, lambda_context):
    """Test that test mode returns 200 without sending email."""
    event = create_contact_event()
    event["headers"] = {"x-test-mode": "true"}
    response = contact_handler.handler(event, lambda_context)
    assert response['statusCode'] == 200


def test_handle_contact_post_in_test_mode_returns_test_mode_true(
    contact_handler, lambda_context
):
    """Test that test mode response includes test_mode true."""
    event = create_contact_event()
    event["headers"] = {"x-test-mode": "true"}
    response = contact_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    test_mode_is_true = body["test_mode"] is True
    assert test_mode_is_true


def test_validate_contact_email_with_valid_email_returns_true(contact_handler):
    """Test that valid email address returns true."""
    result = contact_handler.validate_contact_email("test@example.com")
    assert result


def test_validate_contact_email_with_invalid_email_returns_false(contact_handler):
    """Test that invalid email address returns false."""
    result = contact_handler.validate_contact_email("not-an-email")
    result_is_false = result is False
    assert result_is_false


def test_validate_contact_email_with_empty_string_returns_false(contact_handler):
    """Test that empty string email returns false."""
    result = contact_handler.validate_contact_email("")
    result_is_false = result is False
    assert result_is_false


def test_verify_recaptcha_with_empty_token_returns_false(contact_handler):
    """Test that empty reCAPTCHA token returns false."""
    result = contact_handler.verify_recaptcha("", "secret")
    result_is_false = result is False
    assert result_is_false


def test_verify_recaptcha_with_empty_secret_returns_false(contact_handler):
    """Test that empty reCAPTCHA secret returns false."""
    result = contact_handler.verify_recaptcha("token", "")
    result_is_false = result is False
    assert result_is_false


def test_get_ses_client_returns_client(contact_handler):
    """Test that get_ses_client returns a client."""
    with patch("boto3.client") as mock_boto:
        mock_ses = MagicMock()
        mock_boto.return_value = mock_ses
        with patch.dict(contact_handler.__dict__.get("_clients", {}), clear=True):
            client = contact_handler.get_ses_client()
            client_is_not_none = client is not None
            assert client_is_not_none


def test_send_contact_email_calls_ses_send_email(contact_handler):
    """Test that send_contact_email calls SES send_email."""
    mock_ses = MagicMock()
    with patch.object(contact_handler, "get_ses_client", return_value=mock_ses):
        contact_handler.send_contact_email(
            "to@test.com", "John", "from@test.com", "Hello"
        )
        mock_ses.send_email.assert_called_once()
    assert True  # Explicit pass


def test_send_contact_email_returns_true_on_success(contact_handler):
    """Test that send_contact_email returns true on success."""
    mock_ses = MagicMock()
    with patch.object(contact_handler, "get_ses_client", return_value=mock_ses):
        result = contact_handler.send_contact_email(
            "to@test.com", "John", "from@test.com", "Hello"
        )
        assert result


def test_send_contact_email_returns_false_on_client_error(contact_handler):
    """Test that send_contact_email returns false on ClientError."""
    mock_ses = MagicMock()
    mock_ses.send_email.side_effect = ClientError(
        {"Error": {"Code": "MessageRejected", "Message": "Test error"}},
        "SendEmail"
    )
    with patch.object(contact_handler, "get_ses_client", return_value=mock_ses):
        result = contact_handler.send_contact_email(
            "to@test.com", "John", "from@test.com", "Hello"
        )
        result_is_false = result is False
        assert result_is_false


def test_handler_returns_cors_headers_for_options_request(contact_handler, lambda_context):
    """Test that OPTIONS request returns CORS headers."""
    event = {
        "httpMethod": "OPTIONS",
        "path": "/v1/contact-submissions",
        "headers": {},
        "body": None
    }
    response = contact_handler.handler(event, lambda_context)
    assert response['statusCode'] == 200


def test_handler_returns_cors_allow_origin_header(contact_handler, lambda_context):
    """Test that OPTIONS response includes Allow-Origin header."""
    event = {
        "httpMethod": "OPTIONS",
        "path": "/v1/contact-submissions",
        "headers": {},
        "body": None
    }
    response = contact_handler.handler(event, lambda_context)
    header_is_star = response['headers']['Access-Control-Allow-Origin'] == '*'
    assert header_is_star


def test_handler_returns_404_for_unknown_path(contact_handler, lambda_context):
    """Test that unknown path returns 404."""
    event = {
        "httpMethod": "POST",
        "path": "/v1/unknown",
        "headers": {},
        "body": "{}"
    }
    response = contact_handler.handler(event, lambda_context)
    assert response['statusCode'] == 404
