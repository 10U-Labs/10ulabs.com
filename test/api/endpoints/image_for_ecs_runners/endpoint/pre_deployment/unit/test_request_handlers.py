"""Tests for request handler functions."""
from test.api.endpoints.image_for_ecs_runners.endpoint.test_data import (
    make_ecr_describe_response,
    make_ecr_image_detail,
    make_stable_image,
)

import json
import sys
from unittest.mock import MagicMock, patch

handler = sys.modules['handler']


class TestHandlePostRequest:
    """Tests for handle_post_request function."""

    def test_calls_handler_function(self):
        """Test that handler function is called."""
        mock_handler = MagicMock(return_value={'success': True})
        event = {'body': '{}', 'path': '/v1/test'}

        handler.handle_post_request(event, mock_handler)

        assert mock_handler.called

    def test_passes_parsed_body_to_handler(self):
        """Test that parsed body is passed to handler."""
        mock_handler = MagicMock(return_value={'success': True})
        event = {'body': '{"key": "value"}', 'path': '/v1/test'}

        handler.handle_post_request(event, mock_handler)

        mock_handler.assert_called_with({'key': 'value'})

    def test_returns_success_response(self):
        """Test that success response is returned."""
        mock_handler = MagicMock(return_value={'success': True, 'data': 'test'})
        event = {'body': '{}', 'path': '/v1/test'}

        result = handler.handle_post_request(event, mock_handler)

        assert result['statusCode'] == 200

    def test_returns_error_on_value_error(self):
        """Test that error response is returned on ValueError."""
        mock_handler = MagicMock(side_effect=ValueError('Invalid value'))
        event = {'body': '{}', 'path': '/v1/test'}

        result = handler.handle_post_request(event, mock_handler)

        assert result['statusCode'] == 500

    def test_returns_error_on_key_error(self):
        """Test that error response is returned on KeyError."""
        mock_handler = MagicMock(side_effect=KeyError('missing_key'))
        event = {'body': '{}', 'path': '/v1/test'}

        result = handler.handle_post_request(event, mock_handler)

        assert result['statusCode'] == 500

    def test_returns_mock_response_in_test_mode(self):
        """Test that mock response is returned in test mode."""
        handler.set_test_mode(True)
        mock_handler = MagicMock(return_value={'success': True})
        event = {'body': '{}', 'path': '/v1/image-for-ecs-runners'}

        result = handler.handle_post_request(event, mock_handler)

        body = json.loads(result['body'])
        assert body['test_mode'] is True
        assert mock_handler.called is False


class TestHandleEcsImageGet:
    """Tests for handle_ecs_image_get function."""

    def test_calls_get_latest_for_latest_path(self, mock_ecr_client):
        """Test that get_latest is called for /latest path."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_stable_image(digest='sha256:abc')]
        )
        handler.set_client('ecr', mock_ecr_client)
        event = {'path': '/v1/image-for-ecs-runners/latest'}

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.handle_ecs_image_get(event)

        assert result['statusCode'] == 200

    def test_calls_list_for_base_path(self, mock_ecr_client):
        """Test that list is called for base path."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response()
        handler.set_client('ecr', mock_ecr_client)
        event = {'path': '/v1/image-for-ecs-runners'}

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.handle_ecs_image_get(event)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'images' in body


class TestHandleEcsImageGetByDigest:
    """Tests for handle_ecs_image_get_by_digest function."""

    def test_returns_400_without_digest(self):
        """Test that 400 is returned without digest."""
        event = {'pathParameters': {}}

        result = handler.handle_ecs_image_get_by_digest(event)

        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert 'digest' in body['error'].lower()

    def test_returns_400_with_none_path_parameters(self):
        """Test that 400 is returned with None pathParameters."""
        event = {'pathParameters': None}

        result = handler.handle_ecs_image_get_by_digest(event)

        assert result['statusCode'] == 400

    def test_returns_image_by_digest(self, mock_ecr_client):
        """Test that image is returned by digest."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_ecr_image_detail(digest='sha256:abc123')]
        )
        handler.set_client('ecr', mock_ecr_client)
        event = {'pathParameters': {'digest': 'sha256:abc123'}}

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.handle_ecs_image_get_by_digest(event)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['digest'] == 'sha256:abc123'

    def test_returns_404_for_not_found(self, mock_ecr_client):
        """Test that 404 is returned when image not found."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response()
        handler.set_client('ecr', mock_ecr_client)
        event = {'pathParameters': {'digest': 'sha256:notfound'}}

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.handle_ecs_image_get_by_digest(event)

        assert result['statusCode'] == 404


class TestHandleEcsImageDelete:
    """Tests for handle_ecs_image_delete function."""

    def test_returns_400_without_digest(self):
        """Test that 400 is returned without digest."""
        event = {'pathParameters': {}}

        result = handler.handle_ecs_image_delete(event)

        assert result['statusCode'] == 400

    def test_deletes_image_by_digest(self, mock_ecr_client):
        """Test that image is deleted by digest."""
        mock_ecr_client.batch_delete_image.return_value = {}
        handler.set_client('ecr', mock_ecr_client)
        event = {'pathParameters': {'digest': 'sha256:abc123'}}

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.handle_ecs_image_delete(event)

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['success'] is True
