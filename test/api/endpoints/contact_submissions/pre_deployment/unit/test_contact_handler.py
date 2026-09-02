import json
import urllib.error
from types import ModuleType
from typing import Any, Dict
from unittest.mock import Mock
from unittest.mock import patch, MagicMock
from lambda_response import parse_response_body

from botocore.exceptions import ClientError


def create_contact_event(
    name: str = "John Doe",
    email: str = "john@example.com",
    message: str = "Hello, this is a test message.",
    recaptcha_token: str = "valid-token",
) -> Dict[str, Any]:
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


def test_handle_contact_post_with_valid_data_returns_200(successful_contact_response: Any) -> None:
    assert successful_contact_response['statusCode'] == 200


def test_handle_contact_post_returns_json_content_type(successful_contact_response: Any) -> None:
    assert successful_contact_response['headers']['Content-Type'].startswith('application/json')


def test_handle_contact_post_with_valid_data_returns_success_true(
    successful_contact_response: Any
) -> None:
    body = parse_response_body(successful_contact_response)
    success_is_true = body["success"] is True
    assert success_is_true


def test_handle_contact_post_with_missing_recaptcha_token_returns_400(
    contact_handler: ModuleType, lambda_context: Mock
) -> None:
    event = create_contact_event(recaptcha_token="")
    response = contact_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_missing_name_returns_400(
    contact_handler: ModuleType,
    lambda_context: Mock
) -> None:
    event = create_contact_event(name="")
    response = contact_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_name_too_long_returns_400(
    contact_handler: ModuleType,
    lambda_context: Mock
) -> None:
    event = create_contact_event(name="x" * 101)
    response = contact_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_missing_email_returns_400(
    contact_handler: ModuleType,
    lambda_context: Mock
) -> None:
    event = create_contact_event(email="")
    response = contact_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_email_too_long_returns_400(
    contact_handler: ModuleType,
    lambda_context: Mock
) -> None:
    event = create_contact_event(email="x" * 256)
    response = contact_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_invalid_email_returns_400(
    contact_handler: ModuleType,
    lambda_context: Mock
) -> None:
    event = create_contact_event(email="not-an-email")
    response = contact_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_missing_message_returns_400(
    contact_handler: ModuleType,
    lambda_context: Mock
) -> None:
    event = create_contact_event(message="")
    response = contact_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_message_too_long_returns_400(
    contact_handler: ModuleType,
    lambda_context: Mock
) -> None:
    event = create_contact_event(message="x" * 1001)
    response = contact_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 400


def test_handle_contact_post_with_failed_recaptcha_returns_400(
    contact_handler: ModuleType,
    lambda_context: Mock
) -> None:
    with patch.object(contact_handler, "get_recaptcha_secret", return_value="secret"):
        with patch.object(contact_handler, "verify_recaptcha", return_value=False):
            with patch.dict("os.environ", {"CONTACT_EMAIL": "contact@test.com"}):
                event = create_contact_event()
                response = contact_handler.lambda_handler(event, lambda_context)
                assert response['statusCode'] == 400


def test_handle_contact_post_with_missing_recaptcha_secret_returns_500(
    contact_handler: ModuleType, lambda_context: Mock
) -> None:
    with patch.object(contact_handler, "get_recaptcha_secret", return_value=""):
        with patch.dict("os.environ", {"CONTACT_EMAIL": "contact@test.com"}):
            event = create_contact_event()
            response = contact_handler.lambda_handler(event, lambda_context)
            assert response['statusCode'] == 500


def test_handle_contact_post_with_missing_contact_email_returns_500(
    contact_handler: ModuleType, lambda_context: Mock
) -> None:
    with patch.object(contact_handler, "get_recaptcha_secret", return_value="secret"):
        with patch.object(contact_handler, "verify_recaptcha", return_value=True):
            with patch.dict("os.environ", {"CONTACT_EMAIL": ""}):
                event = create_contact_event()
                response = contact_handler.lambda_handler(event, lambda_context)
                assert response['statusCode'] == 500


def test_handle_contact_post_with_email_send_failure_returns_500(
    contact_handler: ModuleType, lambda_context: Mock
) -> None:
    with patch.object(contact_handler, "get_recaptcha_secret", return_value="secret"):
        with patch.object(contact_handler, "verify_recaptcha", return_value=True):
            with patch.object(contact_handler, "send_contact_email", return_value=False):
                with patch.dict("os.environ", {"CONTACT_EMAIL": "contact@test.com"}):
                    event = create_contact_event()
                    response = contact_handler.lambda_handler(event, lambda_context)
                    assert response['statusCode'] == 500


def test_handle_contact_post_with_invalid_json_returns_500(
    contact_handler: ModuleType,
    lambda_context: Mock
) -> None:
    event = {
        "httpMethod": "POST",
        "path": "/v1/contact-submissions",
        "headers": {},
        "body": "not valid json",
        "requestContext": {"requestId": "test-id"},
    }
    response = contact_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 500


def test_handle_contact_post_in_test_mode_returns_200(
    contact_handler: ModuleType,
    lambda_context: Mock
) -> None:
    event = create_contact_event()
    event["headers"] = {"x-test-mode": "true"}
    response = contact_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 200


def test_handle_contact_post_in_test_mode_returns_test_mode_true(
    contact_handler: ModuleType, lambda_context: Mock
) -> None:
    event = create_contact_event()
    event["headers"] = {"x-test-mode": "true"}
    response = contact_handler.lambda_handler(event, lambda_context)
    body = parse_response_body(response)
    test_mode_is_true = body["test_mode"] is True
    assert test_mode_is_true


def test_validate_contact_email_with_valid_email_returns_true(contact_handler: ModuleType) -> None:
    result = contact_handler.validate_contact_email("test@example.com")
    assert result


def test_validate_contact_email_with_invalid_email_returns_false(
    contact_handler: ModuleType
) -> None:
    result = contact_handler.validate_contact_email("not-an-email")
    result_is_false = result is False
    assert result_is_false


def test_validate_contact_email_with_empty_string_returns_false(
    contact_handler: ModuleType
) -> None:
    result = contact_handler.validate_contact_email("")
    result_is_false = result is False
    assert result_is_false


def test_verify_recaptcha_with_empty_token_returns_false(contact_handler: ModuleType) -> None:
    result = contact_handler.verify_recaptcha("", "secret")
    result_is_false = result is False
    assert result_is_false


def test_verify_recaptcha_with_empty_secret_returns_false(contact_handler: ModuleType) -> None:
    result = contact_handler.verify_recaptcha("token", "")
    result_is_false = result is False
    assert result_is_false


def test_get_ses_client_returns_client(contact_handler: ModuleType) -> None:
    with patch("boto3.client") as mock_boto:
        mock_ses = MagicMock()
        mock_boto.return_value = mock_ses
        with patch.dict(contact_handler.__dict__.get("_clients", {}), clear=True):
            client = contact_handler.get_ses_client()
            client_is_not_none = client is not None
            assert client_is_not_none


def test_send_contact_email_calls_ses_send_email(contact_handler: ModuleType) -> None:
    mock_ses = MagicMock()
    with patch.object(contact_handler, "get_ses_client", return_value=mock_ses):
        contact_handler.send_contact_email(
            "to@test.com", "John", "from@test.com", "Hello"
        )
        mock_ses.send_email.assert_called_once()
    assert True


def test_send_contact_email_returns_true_on_success(contact_handler: ModuleType) -> None:
    mock_ses = MagicMock()
    with patch.object(contact_handler, "get_ses_client", return_value=mock_ses):
        result = contact_handler.send_contact_email(
            "to@test.com", "John", "from@test.com", "Hello"
        )
        assert result


def test_send_contact_email_returns_false_on_client_error(contact_handler: ModuleType) -> None:
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


def test_handler_returns_cors_headers_for_options_request(
    contact_handler: ModuleType,
    lambda_context: Mock
) -> None:
    event = {
        "httpMethod": "OPTIONS",
        "path": "/v1/contact-submissions",
        "headers": {},
        "body": None
    }
    response = contact_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 200


def test_handler_returns_cors_allow_origin_header(
    contact_handler: ModuleType,
    lambda_context: Mock
) -> None:
    event = {
        "httpMethod": "OPTIONS",
        "path": "/v1/contact-submissions",
        "headers": {},
        "body": None
    }
    response = contact_handler.lambda_handler(event, lambda_context)
    header_is_star = response['headers']['Access-Control-Allow-Origin'] == '*'
    assert header_is_star


def test_handler_returns_404_for_unknown_path(
    contact_handler: ModuleType,
    lambda_context: Mock
) -> None:
    event = {
        "httpMethod": "POST",
        "path": "/v1/unknown",
        "headers": {},
        "body": "{}"
    }
    response = contact_handler.lambda_handler(event, lambda_context)
    assert response['statusCode'] == 404


def test_get_header_case_insensitive_with_none_value(contact_handler: ModuleType) -> None:
    headers = {"X-Test-Header": None}
    result = contact_handler.get_header_case_insensitive(headers, "x-test-header")
    assert result == ''


def test_get_header_case_insensitive_header_not_found(contact_handler: ModuleType) -> None:
    headers = {"X-Some-Other-Header": "value"}
    result = contact_handler.get_header_case_insensitive(headers, "x-test-header")
    assert result == ''


def test_get_ssm_client_creates_client_when_not_cached(contact_handler: ModuleType) -> None:
    with patch("boto3.client") as mock_boto:
        mock_ssm = MagicMock()
        mock_boto.return_value = mock_ssm
        clients_dict = vars(contact_handler).get("_clients", {})
        clients_dict.pop("ssm", None)
        client = contact_handler.get_ssm_client()
        client_is_not_none = client is not None
        assert client_is_not_none


def test_get_recaptcha_secret_returns_secret_from_ssm(contact_handler: ModuleType) -> None:
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {
        "Parameter": {"Value": "test-secret-key"}
    }
    with patch.object(contact_handler, "get_ssm_client", return_value=mock_ssm):
        with patch.dict("os.environ", {"RECAPTCHA_SECRET_PARAMETER_NAME": "/test/param"}):
            result = contact_handler.get_recaptcha_secret()
            assert result == "test-secret-key"


def test_get_recaptcha_secret_returns_empty_when_no_parameter_name(
    contact_handler: ModuleType
) -> None:
    with patch.dict("os.environ", {"RECAPTCHA_SECRET_PARAMETER_NAME": ""}):
        result = contact_handler.get_recaptcha_secret()
        assert result == ""


def test_get_recaptcha_secret_returns_empty_on_client_error(contact_handler: ModuleType) -> None:
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.side_effect = ClientError(
        {"Error": {"Code": "ParameterNotFound", "Message": "Not found"}},
        "GetParameter"
    )
    with patch.object(contact_handler, "get_ssm_client", return_value=mock_ssm):
        with patch.dict("os.environ", {"RECAPTCHA_SECRET_PARAMETER_NAME": "/test/param"}):
            result = contact_handler.get_recaptcha_secret()
            assert result == ""


def test_get_recaptcha_secret_returns_empty_on_key_error(contact_handler: ModuleType) -> None:
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {"Parameter": {}}
    with patch.object(contact_handler, "get_ssm_client", return_value=mock_ssm):
        with patch.dict("os.environ", {"RECAPTCHA_SECRET_PARAMETER_NAME": "/test/param"}):
            result = contact_handler.get_recaptcha_secret()
            assert result == ""


def test_verify_recaptcha_returns_true_on_success(contact_handler: ModuleType) -> None:
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"success": true, "score": 0.9}'
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = contact_handler.verify_recaptcha("test-token", "test-secret")
        assert result is True


def test_verify_recaptcha_returns_false_on_low_score(contact_handler: ModuleType) -> None:
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"success": true, "score": 0.3}'
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = contact_handler.verify_recaptcha("test-token", "test-secret")
        result_is_false = result is False
        assert result_is_false


def test_verify_recaptcha_returns_false_on_success_false(contact_handler: ModuleType) -> None:
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"success": false, "score": 0.9}'
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = contact_handler.verify_recaptcha("test-token", "test-secret")
        result_is_false = result is False
        assert result_is_false


def test_verify_recaptcha_returns_false_on_url_error(contact_handler: ModuleType) -> None:
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.URLError("Connection failed")
        result = contact_handler.verify_recaptcha("test-token", "test-secret")
        result_is_false = result is False
        assert result_is_false


def test_verify_recaptcha_returns_false_on_http_error(contact_handler: ModuleType) -> None:
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "http://test", 500, "Server Error", {}, None
        )
        result = contact_handler.verify_recaptcha("test-token", "test-secret")
        result_is_false = result is False
        assert result_is_false


def test_verify_recaptcha_returns_false_on_os_error(contact_handler: ModuleType) -> None:
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = OSError("Network error")
        result = contact_handler.verify_recaptcha("test-token", "test-secret")
        result_is_false = result is False
        assert result_is_false


def test_verify_recaptcha_returns_false_on_json_decode_error(contact_handler: ModuleType) -> None:
    mock_response = MagicMock()
    mock_response.read.return_value = b'not valid json'
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = contact_handler.verify_recaptcha("test-token", "test-secret")
        result_is_false = result is False
        assert result_is_false
