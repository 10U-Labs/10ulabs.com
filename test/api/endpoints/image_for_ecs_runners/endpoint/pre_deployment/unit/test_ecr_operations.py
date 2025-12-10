"""Tests for ECR operations in the handler."""
from test.api.endpoints.image_for_ecs_runners.endpoint.test_data import (
    make_ecr_describe_response,
    make_ecr_image_detail,
    make_stable_image,
)

import sys
from datetime import datetime, timezone
from unittest.mock import patch

from botocore.exceptions import ClientError

handler = sys.modules['handler']


class TestListEcrImages:
    """Tests for list_ecr_images function."""

    def test_returns_success_with_images(self, mock_ecr_client):
        """Test that images are listed successfully."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_ecr_image_detail(digest='sha256:abc123', tags=['latest', 'v1.0'])]
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.list_ecr_images()

        assert result['success'] is True
        assert result['count'] == 1
        assert result['repository'] == 'test-repo'
        assert len(result['images']) == 1

    def test_returns_image_details(self, mock_ecr_client):
        """Test that image details are included."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_ecr_image_detail(digest='sha256:abc123', tags=['latest'])]
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.list_ecr_images()

        image = result['images'][0]
        assert image['digest'] == 'sha256:abc123'
        assert image['tags'] == ['latest']
        assert image['size_bytes'] == 1024

    def test_filters_tagged_images_only(self, mock_ecr_client):
        """Test that only tagged images are requested."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response()
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            handler.list_ecr_images()

        mock_ecr_client.describe_images.assert_called_with(
            repositoryName='test-repo',
            filter={'tagStatus': 'TAGGED'}
        )

    def test_skips_images_without_tags(self, mock_ecr_client):
        """Test that images without tags are skipped."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_ecr_image_detail(tags=[])]
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.list_ecr_images()

        assert result['count'] == 0
        assert len(result['images']) == 0

    def test_sorts_images_by_pushed_at_descending(self, mock_ecr_client):
        """Test that images are sorted by pushed_at descending."""
        older_image = make_ecr_image_detail(
            digest='sha256:older', tags=['v1.0'],
            pushed_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )
        newer_image = make_ecr_image_detail(
            digest='sha256:newer', tags=['v2.0'],
            pushed_at=datetime(2024, 6, 1, tzinfo=timezone.utc)
        )
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [older_image, newer_image]
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.list_ecr_images()

        assert result['images'][0]['digest'] == 'sha256:newer'
        assert result['images'][1]['digest'] == 'sha256:older'

    def test_returns_error_on_client_error(self, mock_ecr_client):
        """Test that ClientError is handled."""
        mock_ecr_client.describe_images.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'DescribeImages'
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.list_ecr_images()

        assert result['success'] is False
        assert 'error' in result


class TestGetLatestEcrImage:
    """Tests for get_latest_ecr_image function."""

    def test_returns_stable_image(self, mock_ecr_client):
        """Test that stable image is returned."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_stable_image(digest='sha256:stable123', additional_tags=['v1.0'])]
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.get_latest_ecr_image()

        assert result['success'] is True
        assert result['digest'] == 'sha256:stable123'
        assert 'stable' in result['tags']

    def test_ignores_non_stable_images(self, mock_ecr_client):
        """Test that non-stable images are ignored."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_ecr_image_detail(digest='sha256:latest123', tags=['latest'])]
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.get_latest_ecr_image()

        assert result['success'] is False
        assert result['error'] == 'No stable image found'

    def test_returns_most_recent_stable_image(self, mock_ecr_client):
        """Test that most recent stable image is returned."""
        older_stable = make_stable_image(digest='sha256:older', additional_tags=['v1.0'])
        older_stable['imagePushedAt'] = datetime(2024, 1, 1, tzinfo=timezone.utc)
        newer_stable = make_stable_image(digest='sha256:newer', additional_tags=['v2.0'])
        newer_stable['imagePushedAt'] = datetime(2024, 6, 1, tzinfo=timezone.utc)
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [older_stable, newer_stable]
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.get_latest_ecr_image()

        assert result['digest'] == 'sha256:newer'

    def test_returns_error_on_client_error(self, mock_ecr_client):
        """Test that ClientError is handled."""
        mock_ecr_client.describe_images.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'DescribeImages'
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.get_latest_ecr_image()

        assert result['success'] is False


class TestGetEcrImageByDigest:
    """Tests for get_ecr_image_by_digest function."""

    def test_returns_image_by_digest(self, mock_ecr_client):
        """Test that image is returned by digest."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_ecr_image_detail(digest='sha256:abc123')]
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.get_ecr_image_by_digest('sha256:abc123')

        assert result['success'] is True
        assert result['digest'] == 'sha256:abc123'

    def test_passes_correct_digest_to_api(self, mock_ecr_client):
        """Test that correct digest is passed to API."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_ecr_image_detail(digest='sha256:abc123')]
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            handler.get_ecr_image_by_digest('sha256:abc123')

        mock_ecr_client.describe_images.assert_called_with(
            repositoryName='test-repo',
            imageIds=[{'imageDigest': 'sha256:abc123'}]
        )

    def test_returns_error_for_not_found(self, mock_ecr_client):
        """Test that error is returned when image not found."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response()
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.get_ecr_image_by_digest('sha256:notfound')

        assert result['success'] is False
        assert 'not found' in result['error']

    def test_returns_error_on_image_not_found_exception(self, mock_ecr_client):
        """Test that ImageNotFoundException is handled."""
        mock_ecr_client.describe_images.side_effect = ClientError(
            {'Error': {'Code': 'ImageNotFoundException', 'Message': 'Image not found'}},
            'DescribeImages'
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.get_ecr_image_by_digest('sha256:notfound')

        assert result['success'] is False
        assert 'not found' in result['error']

    def test_returns_error_on_other_client_error(self, mock_ecr_client):
        """Test that other ClientErrors are handled."""
        mock_ecr_client.describe_images.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'DescribeImages'
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.get_ecr_image_by_digest('sha256:abc123')

        assert result['success'] is False

    def test_handles_image_without_tags(self, mock_ecr_client):
        """Test that image without tags returns empty list."""
        image_no_tags = make_ecr_image_detail(digest='sha256:abc123')
        del image_no_tags['imageTags']
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [image_no_tags]
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.get_ecr_image_by_digest('sha256:abc123')

        assert result['success'] is True
        assert result['tags'] == []


class TestDeleteEcrImage:
    """Tests for delete_ecr_image function."""

    def test_deletes_image_successfully(self, mock_ecr_client):
        """Test that image is deleted successfully."""
        mock_ecr_client.batch_delete_image.return_value = {}
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.delete_ecr_image('sha256:abc123')

        assert result['success'] is True
        assert result['digest'] == 'sha256:abc123'
        assert 'deleted' in result['message'].lower()

    def test_passes_correct_digest_to_api(self, mock_ecr_client):
        """Test that correct digest is passed to API."""
        mock_ecr_client.batch_delete_image.return_value = {}
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            handler.delete_ecr_image('sha256:abc123')

        mock_ecr_client.batch_delete_image.assert_called_with(
            repositoryName='test-repo',
            imageIds=[{'imageDigest': 'sha256:abc123'}]
        )

    def test_returns_error_on_client_error(self, mock_ecr_client):
        """Test that ClientError is handled."""
        mock_ecr_client.batch_delete_image.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'BatchDeleteImage'
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.delete_ecr_image('sha256:abc123')

        assert result['success'] is False
        assert 'error' in result
