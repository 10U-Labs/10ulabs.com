"""Tests for lambda_handler routing and main entry point."""
from test.api.endpoints.runners.ecs.images.endpoint.test_data import (
    make_ecr_describe_response,
    make_ecr_image_detail,
)

import json
import sys
from unittest.mock import patch

handler = sys.modules['handler']


class TestLambdaHandlerOptions:
    """Tests for OPTIONS request handling."""

    def test_returns_200_for_options(self, make_api_event):
        """Test that 200 is returned for OPTIONS."""
        event = make_api_event(method='OPTIONS')

        result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 200

    def test_includes_cors_allow_origin_header(self, make_api_event):
        """Test that CORS Allow-Origin header is included for OPTIONS."""
        event = make_api_event(method='OPTIONS')

        result = handler.lambda_handler(event, None)

        assert result['headers']['Access-Control-Allow-Origin'] == '*'

    def test_includes_get_in_allowed_methods(self, make_api_event):
        """Test that GET is in allowed methods for OPTIONS."""
        event = make_api_event(method='OPTIONS')

        result = handler.lambda_handler(event, None)

        assert 'GET' in result['headers']['Access-Control-Allow-Methods']

    def test_includes_post_in_allowed_methods(self, make_api_event):
        """Test that POST is in allowed methods for OPTIONS."""
        event = make_api_event(method='OPTIONS')

        result = handler.lambda_handler(event, None)

        assert 'POST' in result['headers']['Access-Control-Allow-Methods']

    def test_includes_delete_in_allowed_methods(self, make_api_event):
        """Test that DELETE is in allowed methods for OPTIONS."""
        event = make_api_event(method='OPTIONS')

        result = handler.lambda_handler(event, None)

        assert 'DELETE' in result['headers']['Access-Control-Allow-Methods']

    def test_returns_empty_body_for_options(self, make_api_event):
        """Test that empty body is returned for OPTIONS."""
        event = make_api_event(method='OPTIONS')

        result = handler.lambda_handler(event, None)

        assert result['body'] == ''


class TestLambdaHandlerTestMode:
    """Tests for test mode header handling."""

    def test_enables_test_mode_with_header(self, make_api_event):
        """Test that test mode is enabled with header."""
        event = make_api_event(method='OPTIONS', headers={'x-test-mode': 'true'})

        handler.lambda_handler(event, None)

        assert handler.is_test_mode() is True

    def test_test_mode_case_insensitive_header(self, make_api_event):
        """Test that test mode header is case insensitive."""
        event = make_api_event(method='OPTIONS', headers={'X-Test-Mode': 'true'})

        handler.lambda_handler(event, None)

        assert handler.is_test_mode() is True

    def test_test_mode_disabled_without_header(self, make_api_event):
        """Test that test mode is disabled without header."""
        event = make_api_event(method='OPTIONS')

        handler.lambda_handler(event, None)

        assert handler.is_test_mode() is False


class TestLambdaHandlerRouting:
    """Tests for request routing."""

    def test_routes_get_to_list_images_returns_200(self, mock_ecr_client, make_api_event):
        """Test that GET returns 200 status."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response()
        handler.set_client('ecr', mock_ecr_client)
        event = make_api_event()

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 200

    def test_routes_get_to_list_images_returns_images(self, mock_ecr_client, make_api_event):
        """Test that GET returns images in body."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response()
        handler.set_client('ecr', mock_ecr_client)
        event = make_api_event()

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.lambda_handler(event, None)

        body = json.loads(result['body'])
        assert 'images' in body

    def test_routes_get_latest_returns_200(self, call_latest_endpoint):
        """Test that GET /latest returns 200 status."""
        result = call_latest_endpoint()

        assert result['statusCode'] == 200

    def test_routes_get_latest_returns_digest(self, call_latest_endpoint):
        """Test that GET /latest returns correct digest."""
        result = call_latest_endpoint()

        body = json.loads(result['body'])
        assert body['digest'] == 'sha256:abc'

    def test_routes_get_digest_to_get_by_digest(self, mock_ecr_client, make_api_event):
        """Test that GET /{digest} is routed to get by digest."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_ecr_image_detail(digest='sha256:abc123')]
        )
        handler.set_client('ecr', mock_ecr_client)
        event = make_api_event(
            path='/v1/runners/ecs/images/sha256:abc123',
            path_params={'digest': 'sha256:abc123'}
        )

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 200

    def test_routes_delete_to_delete_image(self, mock_ecr_client, make_api_event):
        """Test that DELETE /{digest} is routed to delete image."""
        mock_ecr_client.batch_delete_image.return_value = {}
        handler.set_client('ecr', mock_ecr_client)
        event = make_api_event(
            method='DELETE',
            path='/v1/runners/ecs/images/sha256:abc123',
            path_params={'digest': 'sha256:abc123'}
        )

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 200

    def test_routes_post_to_trigger_build(self, make_api_event):
        """Test that POST is routed to trigger build."""
        mock_response = type('Response', (), {
            'status': 204,
            '__enter__': lambda self: self,
            '__exit__': lambda self, *args: False
        })()

        with patch('handler.get_github_token', return_value='token'):
            with patch('urllib.request.urlopen', return_value=mock_response):
                with patch.dict('os.environ', {
                    'GITHUB_REPO': 'org/repo',
                    'GITHUB_TOKEN_SECRET_NAME': '/github/token'
                }):
                    event = make_api_event(method='POST', body='{}')
                    result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 200

    def test_returns_404_for_unknown_path(self, make_api_event):
        """Test that 404 is returned for unknown path."""
        event = make_api_event(path='/v1/unknown')

        result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 404

    def test_returns_404_for_unknown_method(self, make_api_event):
        """Test that 404 is returned for unknown method."""
        event = make_api_event(method='PATCH')

        result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 404


class TestLambdaHandlerEdgeCases:
    """Tests for edge cases in lambda handler."""

    def test_handles_missing_headers(self, mock_ecr_client):
        """Test that missing headers are handled."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response()
        handler.set_client('ecr', mock_ecr_client)
        event = {'httpMethod': 'GET', 'path': '/v1/runners/ecs/images'}

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 200

    def test_handles_empty_event(self):
        """Test that empty event is handled."""
        result = handler.lambda_handler({}, None)

        assert result['statusCode'] == 404

    def test_handles_missing_path(self):
        """Test that missing path is handled."""
        event = {'httpMethod': 'GET', 'headers': {}}

        result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 404
