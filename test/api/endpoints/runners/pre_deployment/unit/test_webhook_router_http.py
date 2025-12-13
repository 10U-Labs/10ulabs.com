"""Unit tests for webhook router HTTP utilities."""
import json
import urllib.error
from unittest.mock import patch, MagicMock


def test_make_http_request_with_retry_succeeds_on_first_attempt(webhook_router):
    """Test make http request with retry succeeds on first attempt."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'result': 'success'}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        result = webhook_router.make_http_request_with_retry('http://test.com', {})
        success, _data, _error, _status = result
    assert success is True


def test_make_http_request_with_retry_retries_on_server_error_returns_false(webhook_router):
    """Test make http request with retry retries on server error returns false."""
    with patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 500, 'Server Error', {}, None)
        result = webhook_router.make_http_request_with_retry(
            'http://test.com', {}, max_retries=1
        )
        success, _data, _error, _status = result
    assert success is False


def test_make_http_request_with_retry_retries_on_server_error_returns_status_code(webhook_router):
    """Test make http request with retry retries on server error returns status code."""
    with patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 500, 'Server Error', {}, None)
        result = webhook_router.make_http_request_with_retry(
            'http://test.com', {}, max_retries=1
        )
        _success, _data, _error, status = result
    assert status == 500


def test_make_http_request_with_retry_fails_immediately_on_client_error_returns_false(
    webhook_router
):
    """Test make http request with retry fails immediately on client error returns false."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 400, 'Bad Request', {}, None)
        result = webhook_router.make_http_request_with_retry('http://test.com', {})
        success, _data, _error, _status = result
    assert success is False


def test_make_http_request_with_retry_fails_immediately_on_client_error_returns_status_code(
    webhook_router
):
    """Test make http request with retry fails immediately on client error returns status code."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 400, 'Bad Request', {}, None)
        result = webhook_router.make_http_request_with_retry('http://test.com', {})
        _success, _data, _error, status = result
    assert status == 400


def test_make_http_request_with_retry_returns_503_returns_false(webhook_router):
    """Test make http request with retry returns 503 returns false."""
    with patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        http_error = urllib.error.HTTPError('url', 503, 'Service Unavailable', {}, None)
        mock_urlopen.side_effect = http_error
        result = webhook_router.make_http_request_with_retry(
            'http://test.com', {}, max_retries=1
        )
        success, _data, _error, _status = result
    assert success is False


def test_make_http_request_with_retry_returns_503_status_code(webhook_router):
    """Test make http request with retry returns 503 status code."""
    with patch('urllib.request.urlopen') as mock_urlopen, patch('time.sleep'):
        http_error = urllib.error.HTTPError('url', 503, 'Service Unavailable', {}, None)
        mock_urlopen.side_effect = http_error
        result = webhook_router.make_http_request_with_retry(
            'http://test.com', {}, max_retries=1
        )
        _success, _data, _error, status = result
    assert status == 503


def test_should_record_circuit_breaker_failure_returns_false_for_503(webhook_router):
    """Test should record circuit breaker failure returns false for 503."""
    assert webhook_router.should_record_circuit_breaker_failure(503) is False


def test_should_record_circuit_breaker_failure_returns_false_for_500(webhook_router):
    """Test should record circuit breaker failure returns false for 500.

    Any HTTP response means the service is alive, so don't trip the breaker.
    """
    assert webhook_router.should_record_circuit_breaker_failure(500) is False


def test_should_record_circuit_breaker_failure_returns_false_for_502(webhook_router):
    """Test should record circuit breaker failure returns false for 502.

    Any HTTP response means the service is alive, so don't trip the breaker.
    """
    assert webhook_router.should_record_circuit_breaker_failure(502) is False


def test_should_record_circuit_breaker_failure_returns_false_for_504(webhook_router):
    """Test should record circuit breaker failure returns false for 504.

    Any HTTP response means the service is alive, so don't trip the breaker.
    """
    assert webhook_router.should_record_circuit_breaker_failure(504) is False


def test_should_record_circuit_breaker_failure_returns_false_for_400(webhook_router):
    """Test should record circuit breaker failure returns false for 400."""
    assert webhook_router.should_record_circuit_breaker_failure(400) is False


def test_should_record_circuit_breaker_failure_returns_false_for_200(webhook_router):
    """Test should record circuit breaker failure returns false for 200."""
    assert webhook_router.should_record_circuit_breaker_failure(200) is False


def test_should_record_circuit_breaker_failure_returns_true_for_none(webhook_router):
    """Test should record circuit breaker failure returns true for none."""
    assert webhook_router.should_record_circuit_breaker_failure(None) is True
