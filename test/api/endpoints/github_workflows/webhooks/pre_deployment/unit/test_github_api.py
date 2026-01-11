"""Unit tests for github_api module."""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from urllib_mocks import create_mock_urllib_response

from .conftest import load_lambda_module


@pytest.fixture(name="github_api_module")
def github_api_module_fixture():
    """Load github_api module for testing."""
    with patch('boto3.client') as mock_boto_client:
        mock_boto_client.return_value = MagicMock()
        module = load_lambda_module("common/github_api.py", "github_api")
        # Clear cache between tests
        module._cache["token"] = None
        yield module


class TestGetGithubToken:
    """Tests for get_github_token function."""

    def test_returns_cached_token(self, github_api_module):
        """Test that cached token is returned."""
        github_api_module._cache["token"] = "cached-token"
        result = github_api_module.get_github_token()
        assert result == "cached-token"

    def test_returns_empty_when_no_env_var(self, github_api_module):
        """Test that empty string is returned when env var not set."""
        with patch.dict('os.environ', {}, clear=True):
            result = github_api_module.get_github_token()
            assert result == ""

    def test_retrieves_token_from_ssm(self, github_api_module):
        """Test that token is retrieved from SSM."""
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {
            "Parameter": {"Value": "ssm-token"}
        }
        with patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/test/token'}):
            with patch.object(github_api_module, 'get_ssm_client', return_value=mock_ssm):
                result = github_api_module.get_github_token()
                assert result == "ssm-token"
                mock_ssm.get_parameter.assert_called_once_with(
                    Name='/test/token', WithDecryption=True
                )

    def test_caches_retrieved_token(self, github_api_module):
        """Test that retrieved token is cached."""
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {
            "Parameter": {"Value": "new-token"}
        }
        with patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/test/token'}):
            with patch.object(github_api_module, 'get_ssm_client', return_value=mock_ssm):
                github_api_module.get_github_token()
                assert github_api_module._cache["token"] == "new-token"

    def test_returns_empty_on_client_error(self, github_api_module):
        """Test that empty string is returned on ClientError."""
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = ClientError(
            {"Error": {"Code": "ParameterNotFound", "Message": "Not found"}},
            "GetParameter"
        )
        with patch.dict('os.environ', {'GITHUB_TOKEN_SECRET_NAME': '/test/token'}):
            with patch.object(github_api_module, 'get_ssm_client', return_value=mock_ssm):
                result = github_api_module.get_github_token()
                assert result == ""


class TestClearTokenCache:
    """Tests for clear_token_cache function."""

    def test_clears_cached_token(self, github_api_module):
        """Test that cached token is cleared."""
        github_api_module._cache["token"] = "some-token"
        github_api_module.clear_token_cache()
        assert github_api_module._cache["token"] is None


class TestGithubApiRequest:
    """Tests for github_api_request function."""

    def test_get_request_success(self, github_api_module):
        """Test successful GET request."""
        response_data = {"id": 123, "name": "test"}
        mock_response = create_mock_urllib_response(json_data=response_data)

        with patch.object(github_api_module.urllib.request, 'urlopen', return_value=mock_response):
            result = github_api_module.github_api_request("GET", "/test/path", token="test-token")
            assert result == response_data

    def test_post_request_with_data(self, github_api_module):
        """Test POST request with data."""
        response_data = {"success": True}
        mock_response = create_mock_urllib_response(json_data=response_data)
        urlopen_patch = patch.object(
            github_api_module.urllib.request, 'urlopen', return_value=mock_response
        )
        with urlopen_patch as mock_urlopen:
            result = github_api_module.github_api_request(
                "POST", "/test/path", data={"key": "value"}, token="test-token"
            )
            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            assert result == response_data and request.data == b'{"key": "value"}'

    def test_returns_empty_dict_on_empty_response(self, github_api_module):
        """Test that empty dict is returned when response body is empty."""
        mock_response = create_mock_urllib_response(read_value=b'')
        urlopen_patch = patch.object(
            github_api_module.urllib.request, 'urlopen', return_value=mock_response
        )
        with urlopen_patch:
            result = github_api_module.github_api_request(
                "DELETE", "/test/path", token="test-token"
            )
            assert result == {}

    def test_uses_cached_token_when_none_provided(self, github_api_module):
        """Test that cached token is used when no token provided."""
        github_api_module._cache["token"] = "cached-token"
        mock_response = create_mock_urllib_response()
        urlopen_patch = patch.object(
            github_api_module.urllib.request, 'urlopen', return_value=mock_response
        )
        with urlopen_patch as mock_urlopen:
            github_api_module.github_api_request("GET", "/test/path")
            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            assert request.get_header('Authorization') == 'Bearer cached-token'

    def test_raises_http_error(self, github_api_module):
        """Test that HTTPError is raised on failure."""
        error = urllib.error.HTTPError(
            url="https://api.github.com/test",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=MagicMock(read=MagicMock(return_value=b'{"message": "Not found"}'))
        )
        with patch.object(github_api_module.urllib.request, 'urlopen', side_effect=error):
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                github_api_module.github_api_request("GET", "/test/path", token="test-token")
            assert exc_info.value.code == 404

    def test_sets_correct_headers(self, github_api_module):
        """Test that correct headers are set."""
        mock_response = create_mock_urllib_response()
        urlopen_patch = patch.object(
            github_api_module.urllib.request, 'urlopen', return_value=mock_response
        )
        with urlopen_patch as mock_urlopen:
            github_api_module.github_api_request("GET", "/test/path", token="test-token")
            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            expected = ('application/vnd.github+json', '2022-11-28', 'TenULabs-Lambda')
            actual = (
                request.get_header('Accept'),
                request.get_header('X-github-api-version'),
                request.get_header('User-agent')
            )
            assert actual == expected

    def test_no_auth_header_when_no_token(self, github_api_module):
        """Test that no auth header is set when no token available."""
        github_api_module._cache["token"] = None
        mock_response = create_mock_urllib_response()
        urlopen_patch = patch.object(
            github_api_module.urllib.request, 'urlopen', return_value=mock_response
        )
        with patch.dict('os.environ', {}, clear=True), urlopen_patch as mock_urlopen:
            github_api_module.github_api_request("GET", "/test/path")
            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            assert request.get_header('Authorization') is None

    def test_http_error_without_body(self, github_api_module):
        """Test HTTPError handling when fp is None."""
        error = urllib.error.HTTPError(
            url="https://api.github.com/test",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=None
        )
        with patch.object(github_api_module.urllib.request, 'urlopen', side_effect=error):
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                github_api_module.github_api_request("GET", "/test/path", token="test-token")
            assert exc_info.value.code == 500
