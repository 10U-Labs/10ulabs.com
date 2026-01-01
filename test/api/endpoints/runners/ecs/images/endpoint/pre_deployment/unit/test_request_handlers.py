"""Tests for request handler functions."""
from test.api.endpoints.runners.ecs.images.endpoint.test_data import (
    make_ecr_describe_response,
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

    def test_returns_test_mode_true_in_test_mode(self):
        """Test that mock response has test_mode true in test mode."""
        handler.set_test_mode(True)
        mock_handler = MagicMock(return_value={'success': True})
        event = {'body': '{}', 'path': '/v1/runners/ecs/images'}

        result = handler.handle_post_request(event, mock_handler)

        body = json.loads(result['body'])
        assert body['test_mode'] is True

    def test_does_not_call_handler_in_test_mode(self):
        """Test that handler is not called in test mode."""
        handler.set_test_mode(True)
        mock_handler = MagicMock(return_value={'success': True})
        event = {'body': '{}', 'path': '/v1/runners/ecs/images'}

        handler.handle_post_request(event, mock_handler)

        assert mock_handler.called is False


class TestHandleEcsImageGet:
    """Tests for handle_ecs_image_get function."""

    def test_calls_get_latest_for_latest_path(self, mock_ecr_client):
        """Test that get_latest is called for /latest path."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_stable_image(digest='sha256:abc')]
        )
        handler.set_client('ecr', mock_ecr_client)
        event = {'path': '/v1/runners/ecs/images/latest'}

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.handle_ecs_image_get(event)

        assert result['statusCode'] == 200

    def test_returns_200_for_base_path(self, mock_ecr_client):
        """Test that 200 is returned for base path."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response()
        handler.set_client('ecr', mock_ecr_client)
        event = {'path': '/v1/runners/ecs/images'}

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.handle_ecs_image_get(event)

        assert result['statusCode'] == 200

    def test_returns_images_list_for_base_path(self, mock_ecr_client):
        """Test that images list is returned for base path."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response()
        handler.set_client('ecr', mock_ecr_client)
        event = {'path': '/v1/runners/ecs/images'}

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.handle_ecs_image_get(event)

        body = json.loads(result['body'])
        assert 'images' in body


class TestHandleEcsImageGetByDigest:
    """Tests for handle_ecs_image_get_by_digest function."""

    def test_returns_400_status_without_digest(self):
        """Test that 400 status code is returned without digest."""
        event = {'pathParameters': {}}

        result = handler.handle_ecs_image_get_by_digest(event)

        assert result['statusCode'] == 400

    def test_returns_digest_error_message_without_digest(self):
        """Test that error mentions digest when digest is missing."""
        event = {'pathParameters': {}}

        result = handler.handle_ecs_image_get_by_digest(event)

        body = json.loads(result['body'])
        assert 'digest' in body['error'].lower()

    def test_returns_400_with_none_path_parameters(self):
        """Test that 400 is returned with None pathParameters."""
        event = {'pathParameters': None}

        result = handler.handle_ecs_image_get_by_digest(event)

        assert result['statusCode'] == 400

    def test_returns_200_for_existing_digest(self, existing_digest_result):
        """Test that 200 is returned for existing digest."""
        assert existing_digest_result['statusCode'] == 200

    def test_returns_correct_digest_in_response(self, existing_digest_result):
        """Test that correct digest is returned in response."""
        body = json.loads(existing_digest_result['body'])
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

    def test_returns_200_on_delete(self, mock_ecr_client):
        """Test that 200 is returned on delete."""
        mock_ecr_client.batch_delete_image.return_value = {}
        handler.set_client('ecr', mock_ecr_client)
        event = {'pathParameters': {'digest': 'sha256:abc123'}}

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.handle_ecs_image_delete(event)

        assert result['statusCode'] == 200

    def test_returns_success_true_on_delete(self, mock_ecr_client):
        """Test that success is true on delete."""
        mock_ecr_client.batch_delete_image.return_value = {}
        handler.set_client('ecr', mock_ecr_client)
        event = {'pathParameters': {'digest': 'sha256:abc123'}}

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.handle_ecs_image_delete(event)

        body = json.loads(result['body'])
        assert body['success'] is True
