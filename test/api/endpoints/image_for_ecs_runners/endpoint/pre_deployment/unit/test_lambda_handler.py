"""Tests for lambda_handler routing and main entry point."""
from test.api.endpoints.image_for_ecs_runners.endpoint.test_data import (
    make_ecr_describe_response,
    make_ecr_image_detail,
    make_stable_image,
)

import json
import sys
from unittest.mock import patch

handler = sys.modules['handler']


class TestLambdaHandlerOptions:
    """Tests for OPTIONS request handling."""

    def test_returns_200_for_options(self):
        """Test that 200 is returned for OPTIONS."""
        event = {'httpMethod': 'OPTIONS', 'path': '/v1/image-for-ecs-runners', 'headers': {}}

        result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 200

    def test_includes_cors_headers_for_options(self):
        """Test that CORS headers are included for OPTIONS."""
        event = {'httpMethod': 'OPTIONS', 'path': '/v1/image-for-ecs-runners', 'headers': {}}

        result = handler.lambda_handler(event, None)

        assert result['headers']['Access-Control-Allow-Origin'] == '*'
        assert 'GET' in result['headers']['Access-Control-Allow-Methods']
        assert 'POST' in result['headers']['Access-Control-Allow-Methods']
        assert 'DELETE' in result['headers']['Access-Control-Allow-Methods']

    def test_returns_empty_body_for_options(self):
        """Test that empty body is returned for OPTIONS."""
        event = {'httpMethod': 'OPTIONS', 'path': '/v1/image-for-ecs-runners', 'headers': {}}

        result = handler.lambda_handler(event, None)

        assert result['body'] == ''


class TestLambdaHandlerTestMode:
    """Tests for test mode header handling."""

    def test_enables_test_mode_with_header(self):
        """Test that test mode is enabled with header."""
        event = {
            'httpMethod': 'OPTIONS',
            'path': '/v1/image-for-ecs-runners',
            'headers': {'x-test-mode': 'true'}
        }

        handler.lambda_handler(event, None)

        assert handler.is_test_mode() is True

    def test_test_mode_case_insensitive_header(self):
        """Test that test mode header is case insensitive."""
        event = {
            'httpMethod': 'OPTIONS',
            'path': '/v1/image-for-ecs-runners',
            'headers': {'X-Test-Mode': 'true'}
        }

        handler.lambda_handler(event, None)

        assert handler.is_test_mode() is True

    def test_test_mode_disabled_without_header(self):
        """Test that test mode is disabled without header."""
        event = {
            'httpMethod': 'OPTIONS',
            'path': '/v1/image-for-ecs-runners',
            'headers': {}
        }

        handler.lambda_handler(event, None)

        assert handler.is_test_mode() is False


class TestLambdaHandlerRouting:
    """Tests for request routing."""

    def test_routes_get_to_list_images(self, mock_ecr_client):
        """Test that GET is routed to list images."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response()
        handler.set_client('ecr', mock_ecr_client)
        event = {
            'httpMethod': 'GET',
            'path': '/v1/image-for-ecs-runners',
            'headers': {}
        }

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'images' in body

    def test_routes_get_latest_to_get_latest_image(self, mock_ecr_client):
        """Test that GET /latest is routed to get latest image."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_stable_image(digest='sha256:abc')]
        )
        handler.set_client('ecr', mock_ecr_client)
        event = {
            'httpMethod': 'GET',
            'path': '/v1/image-for-ecs-runners/latest',
            'headers': {}
        }

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['digest'] == 'sha256:abc'

    def test_routes_get_digest_to_get_by_digest(self, mock_ecr_client):
        """Test that GET /{digest} is routed to get by digest."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_ecr_image_detail(digest='sha256:abc123')]
        )
        handler.set_client('ecr', mock_ecr_client)
        event = {
            'httpMethod': 'GET',
            'path': '/v1/image-for-ecs-runners/sha256:abc123',
            'pathParameters': {'digest': 'sha256:abc123'},
            'headers': {}
        }

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 200

    def test_routes_delete_to_delete_image(self, mock_ecr_client):
        """Test that DELETE /{digest} is routed to delete image."""
        mock_ecr_client.batch_delete_image.return_value = {}
        handler.set_client('ecr', mock_ecr_client)
        event = {
            'httpMethod': 'DELETE',
            'path': '/v1/image-for-ecs-runners/sha256:abc123',
            'pathParameters': {'digest': 'sha256:abc123'},
            'headers': {}
        }

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 200

    def test_routes_post_to_trigger_build(self):
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
                    event = {
                        'httpMethod': 'POST',
                        'path': '/v1/image-for-ecs-runners',
                        'body': '{}',
                        'headers': {}
                    }

                    result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 200

    def test_returns_404_for_unknown_path(self):
        """Test that 404 is returned for unknown path."""
        event = {
            'httpMethod': 'GET',
            'path': '/v1/unknown',
            'headers': {}
        }

        result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 404

    def test_returns_404_for_unknown_method(self):
        """Test that 404 is returned for unknown method."""
        event = {
            'httpMethod': 'PATCH',
            'path': '/v1/image-for-ecs-runners',
            'headers': {}
        }

        result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 404


class TestLambdaHandlerEdgeCases:
    """Tests for edge cases in lambda handler."""

    def test_handles_missing_headers(self, mock_ecr_client):
        """Test that missing headers are handled."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response()
        handler.set_client('ecr', mock_ecr_client)
        event = {
            'httpMethod': 'GET',
            'path': '/v1/image-for-ecs-runners'
        }

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 200

    def test_handles_empty_event(self):
        """Test that empty event is handled."""
        event = {}

        result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 404

    def test_handles_missing_path(self):
        """Test that missing path is handled."""
        event = {'httpMethod': 'GET', 'headers': {}}

        result = handler.lambda_handler(event, None)

        assert result['statusCode'] == 404
