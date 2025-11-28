import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src" / "website" / "lambdas"))

from contact import validate_email, validate_request_body, build_response, handler


def test_validate_email_valid_email():
    assert validate_email("test@example.com") is True


def test_validate_email_invalid_email_no_at():
    assert validate_email("testexample.com") is False


def test_validate_email_invalid_email_no_domain():
    assert validate_email("test@") is False


def test_validate_email_invalid_email_no_tld():
    assert validate_email("test@example") is False


def test_validate_email_empty_string():
    assert validate_email("") is False


def test_validate_request_body_valid():
    body = {"name": "John", "email": "john@example.com", "message": "Hello"}
    is_valid, error = validate_request_body(body)
    assert is_valid is True


def test_validate_request_body_valid_no_error_message():
    body = {"name": "John", "email": "john@example.com", "message": "Hello"}
    _, error = validate_request_body(body)
    assert error is None


def test_validate_request_body_missing_name():
    body = {"email": "john@example.com", "message": "Hello"}
    is_valid, _ = validate_request_body(body)
    assert is_valid is False


def test_validate_request_body_missing_name_error_message():
    body = {"email": "john@example.com", "message": "Hello"}
    _, error = validate_request_body(body)
    assert error == "Name is required"


def test_validate_request_body_empty_name():
    body = {"name": "", "email": "john@example.com", "message": "Hello"}
    is_valid, _ = validate_request_body(body)
    assert is_valid is False


def test_validate_request_body_name_too_long():
    body = {"name": "a" * 101, "email": "john@example.com", "message": "Hello"}
    is_valid, _ = validate_request_body(body)
    assert is_valid is False


def test_validate_request_body_name_too_long_error_message():
    body = {"name": "a" * 101, "email": "john@example.com", "message": "Hello"}
    _, error = validate_request_body(body)
    assert error == "Name must be less than 100 characters"


def test_validate_request_body_missing_email():
    body = {"name": "John", "message": "Hello"}
    is_valid, _ = validate_request_body(body)
    assert is_valid is False


def test_validate_request_body_missing_email_error_message():
    body = {"name": "John", "message": "Hello"}
    _, error = validate_request_body(body)
    assert error == "Email is required"


def test_validate_request_body_invalid_email():
    body = {"name": "John", "email": "invalid", "message": "Hello"}
    is_valid, _ = validate_request_body(body)
    assert is_valid is False


def test_validate_request_body_invalid_email_error_message():
    body = {"name": "John", "email": "invalid", "message": "Hello"}
    _, error = validate_request_body(body)
    assert error == "Invalid email address"


def test_validate_request_body_email_too_long():
    body = {"name": "John", "email": "a" * 250 + "@b.com", "message": "Hello"}
    is_valid, _ = validate_request_body(body)
    assert is_valid is False


def test_validate_request_body_email_too_long_error_message():
    body = {"name": "John", "email": "a" * 250 + "@b.com", "message": "Hello"}
    _, error = validate_request_body(body)
    assert error == "Email must be less than 255 characters"


def test_validate_request_body_missing_message():
    body = {"name": "John", "email": "john@example.com"}
    is_valid, _ = validate_request_body(body)
    assert is_valid is False


def test_validate_request_body_missing_message_error_message():
    body = {"name": "John", "email": "john@example.com"}
    _, error = validate_request_body(body)
    assert error == "Message is required"


def test_validate_request_body_empty_message():
    body = {"name": "John", "email": "john@example.com", "message": ""}
    is_valid, _ = validate_request_body(body)
    assert is_valid is False


def test_validate_request_body_message_too_long():
    body = {"name": "John", "email": "john@example.com", "message": "a" * 1001}
    is_valid, _ = validate_request_body(body)
    assert is_valid is False


def test_validate_request_body_message_too_long_error_message():
    body = {"name": "John", "email": "john@example.com", "message": "a" * 1001}
    _, error = validate_request_body(body)
    assert error == "Message must be less than 1000 characters"


def test_validate_request_body_not_dict():
    body = "not a dict"
    is_valid, _ = validate_request_body(body)
    assert is_valid is False


def test_validate_request_body_not_dict_error_message():
    body = "not a dict"
    _, error = validate_request_body(body)
    assert error == "Invalid request format"


def test_build_response_status_code():
    response = build_response(200, {"message": "OK"})
    assert response["statusCode"] == 200


def test_build_response_content_type_header():
    response = build_response(200, {"message": "OK"})
    assert response["headers"]["Content-Type"] == "application/json"


def test_build_response_cors_origin_header():
    response = build_response(200, {"message": "OK"})
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"


def test_build_response_body_json_encoded():
    response = build_response(200, {"message": "OK"})
    assert response["body"] == '{"message": "OK"}'


def test_handler_options_request_returns_200():
    event = {"httpMethod": "OPTIONS"}
    response = handler(event, None)
    assert response["statusCode"] == 200


@patch.dict("os.environ", {}, clear=True)
def test_handler_missing_contact_email_env_var():
    event = {"httpMethod": "POST", "body": "{}"}
    response = handler(event, None)
    assert response["statusCode"] == 500


@patch.dict("os.environ", {"CONTACT_EMAIL": "contact@example.com"})
def test_handler_missing_body_returns_400():
    event = {"httpMethod": "POST"}
    response = handler(event, None)
    assert response["statusCode"] == 400


@patch.dict("os.environ", {"CONTACT_EMAIL": "contact@example.com"})
def test_handler_empty_body_returns_400():
    event = {"httpMethod": "POST", "body": ""}
    response = handler(event, None)
    assert response["statusCode"] == 400


@patch.dict("os.environ", {"CONTACT_EMAIL": "contact@example.com"})
def test_handler_invalid_json_returns_400():
    event = {"httpMethod": "POST", "body": "not json"}
    response = handler(event, None)
    assert response["statusCode"] == 400


@patch.dict("os.environ", {"CONTACT_EMAIL": "contact@example.com"})
def test_handler_invalid_json_error_message():
    event = {"httpMethod": "POST", "body": "not json"}
    response = handler(event, None)
    body = json.loads(response["body"])
    assert body["error"] == "Invalid JSON"


@patch.dict("os.environ", {"CONTACT_EMAIL": "contact@example.com"})
def test_handler_validation_error_returns_400():
    event = {"httpMethod": "POST", "body": json.dumps({"name": ""})}
    response = handler(event, None)
    assert response["statusCode"] == 400


@patch.dict("os.environ", {"CONTACT_EMAIL": "contact@example.com"})
@patch("contact.boto3")
def test_handler_successful_submission_returns_200(mock_boto3):
    mock_ses = MagicMock()
    mock_boto3.client.return_value = mock_ses
    event = {
        "httpMethod": "POST",
        "body": json.dumps({"name": "John", "email": "john@example.com", "message": "Hello"})
    }
    response = handler(event, None)
    assert response["statusCode"] == 200


@patch.dict("os.environ", {"CONTACT_EMAIL": "contact@example.com"})
@patch("contact.boto3")
def test_handler_successful_submission_sends_email(mock_boto3):
    mock_ses = MagicMock()
    mock_boto3.client.return_value = mock_ses
    event = {
        "httpMethod": "POST",
        "body": json.dumps({"name": "John", "email": "john@example.com", "message": "Hello"})
    }
    handler(event, None)
    mock_ses.send_email.assert_called_once()


@patch.dict("os.environ", {"CONTACT_EMAIL": "contact@example.com"})
@patch("contact.boto3")
def test_handler_ses_error_returns_500(mock_boto3):
    mock_ses = MagicMock()
    mock_ses.send_email.side_effect = Exception("SES error")
    mock_boto3.client.return_value = mock_ses
    event = {
        "httpMethod": "POST",
        "body": json.dumps({"name": "John", "email": "john@example.com", "message": "Hello"})
    }
    response = handler(event, None)
    assert response["statusCode"] == 500


@patch.dict("os.environ", {"CONTACT_EMAIL": "contact@example.com"})
@patch("contact.boto3")
def test_handler_ses_error_error_message(mock_boto3):
    mock_ses = MagicMock()
    mock_ses.send_email.side_effect = Exception("SES error")
    mock_boto3.client.return_value = mock_ses
    event = {
        "httpMethod": "POST",
        "body": json.dumps({"name": "John", "email": "john@example.com", "message": "Hello"})
    }
    response = handler(event, None)
    body = json.loads(response["body"])
    assert body["error"] == "Failed to send message"
