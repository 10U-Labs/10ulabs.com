"""Tests for ECR operations in the handler."""
from test.api.endpoints.runners.ecs.images.endpoint.test_data import (
    make_ecr_describe_response,
    make_ecr_image_detail,
    make_stable_image,
)

import sys
from datetime import datetime, timezone
from unittest.mock import patch

handler = sys.modules['handler']


class TestListEcrImages:
    """Tests for list_ecr_images function."""

    def test_returns_success_true(self, single_image_list_result):
        """Test that success is True when images are listed."""
        assert single_image_list_result['success'] is True

    def test_returns_correct_count(self, single_image_list_result):
        """Test that count matches number of images."""
        assert single_image_list_result['count'] == 1

    def test_returns_repository_name(self, single_image_list_result):
        """Test that repository name is returned."""
        assert single_image_list_result['repository'] == 'test-repo'

    def test_returns_images_list(self, single_image_list_result):
        """Test that images list is returned."""
        assert len(single_image_list_result['images']) == 1

    def test_returns_image_digest(self, single_image_list_result):
        """Test that image digest is included."""
        assert single_image_list_result['images'][0]['digest'] == 'sha256:abc123'

    def test_returns_image_tags(self, single_image_list_result):
        """Test that image tags are included."""
        assert 'latest' in single_image_list_result['images'][0]['tags']

    def test_returns_image_size(self, single_image_list_result):
        """Test that image size is included."""
        assert single_image_list_result['images'][0]['size_bytes'] == 1024

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

    def test_skips_images_without_tags_count_zero(self, mock_ecr_client):
        """Test that count is zero when images have no tags."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_ecr_image_detail(tags=[])]
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.list_ecr_images()

        assert result['count'] == 0

    def test_skips_images_without_tags_empty_list(self, mock_ecr_client):
        """Test that images list is empty when images have no tags."""
        mock_ecr_client.describe_images.return_value = make_ecr_describe_response(
            [make_ecr_image_detail(tags=[])]
        )
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.list_ecr_images()

        assert len(result['images']) == 0

    def test_sorts_images_by_pushed_at_descending_first(self, sorted_images_result):
        """Test that newest image is first."""
        assert sorted_images_result['images'][0]['digest'] == 'sha256:newer'

    def test_sorts_images_by_pushed_at_descending_second(self, sorted_images_result):
        """Test that older image is second."""
        assert sorted_images_result['images'][1]['digest'] == 'sha256:older'

    def test_returns_error_on_client_error_returns_false(
        self, mock_ecr_client, access_denied_error
    ):
        """Test that ClientError returns success=False."""
        mock_ecr_client.describe_images.side_effect = access_denied_error
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.list_ecr_images()

        assert result['success'] is False

    def test_returns_error_on_client_error_includes_error(
        self, mock_ecr_client, access_denied_error
    ):
        """Test that ClientError includes error in result."""
        mock_ecr_client.describe_images.side_effect = access_denied_error
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.list_ecr_images()

        assert 'error' in result


class TestGetLatestEcrImage:
    """Tests for get_latest_ecr_image function."""

    def test_returns_stable_image_success(self, stable_image_result):
        """Test that stable image returns success."""
        assert stable_image_result['success'] is True

    def test_returns_stable_image_digest(self, stable_image_result):
        """Test that stable image returns correct digest."""
        assert stable_image_result['digest'] == 'sha256:stable123'

    def test_returns_stable_image_has_stable_tag(self, stable_image_result):
        """Test that stable image has stable tag."""
        assert 'stable' in stable_image_result['tags']

    def test_ignores_non_stable_images_returns_false(self, no_stable_image_result):
        """Test that non-stable images return success False."""
        assert no_stable_image_result['success'] is False

    def test_ignores_non_stable_images_error_message(self, no_stable_image_result):
        """Test that non-stable images return correct error."""
        assert no_stable_image_result['error'] == 'No stable image found'

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

    def test_returns_error_on_client_error(self, mock_ecr_client, access_denied_error):
        """Test that ClientError is handled."""
        mock_ecr_client.describe_images.side_effect = access_denied_error
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.get_latest_ecr_image()

        assert result['success'] is False


class TestGetEcrImageByDigest:
    """Tests for get_ecr_image_by_digest function."""

    def test_returns_image_by_digest_success(self, image_by_digest_result):
        """Test that image by digest returns success."""
        assert image_by_digest_result['success'] is True

    def test_returns_image_by_digest_correct_digest(self, image_by_digest_result):
        """Test that image by digest returns correct digest."""
        assert image_by_digest_result['digest'] == 'sha256:abc123'

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

    def test_returns_error_for_not_found_success_false(self, image_not_found_result):
        """Test that not found returns success False."""
        assert image_not_found_result['success'] is False

    def test_returns_error_for_not_found_error_message(self, image_not_found_result):
        """Test that not found returns error message."""
        assert 'not found' in image_not_found_result['error']

    def test_returns_error_on_image_not_found_exception_success_false(
        self, image_not_found_exception_result
    ):
        """Test that ImageNotFoundException returns success False."""
        assert image_not_found_exception_result['success'] is False

    def test_returns_error_on_image_not_found_exception_error_message(
        self, image_not_found_exception_result
    ):
        """Test that ImageNotFoundException returns error message."""
        assert 'not found' in image_not_found_exception_result['error']

    def test_returns_error_on_other_client_error(
        self, mock_ecr_client, access_denied_error
    ):
        """Test that other ClientErrors are handled."""
        mock_ecr_client.describe_images.side_effect = access_denied_error
        handler.set_client('ecr', mock_ecr_client)

        with patch.dict('os.environ', {'ECR_REPOSITORY': 'test-repo'}):
            result = handler.get_ecr_image_by_digest('sha256:abc123')

        assert result['success'] is False

    def test_handles_image_without_tags_returns_success(self, image_without_tags_result):
        """Test that image without tags returns success."""
        assert image_without_tags_result['success'] is True

    def test_handles_image_without_tags_returns_empty_list(self, image_without_tags_result):
        """Test that image without tags returns empty list for tags."""
        assert image_without_tags_result['tags'] == []


class TestDeleteEcrImage:
    """Tests for delete_ecr_image function."""

    def test_deletes_image_returns_success(self, delete_image_result):
        """Test that delete returns success=True."""
        assert delete_image_result['success'] is True

    def test_deletes_image_returns_digest(self, delete_image_result):
        """Test that delete returns the deleted digest."""
        assert delete_image_result['digest'] == 'sha256:abc123'

    def test_deletes_image_returns_message(self, delete_image_result):
        """Test that delete returns message containing deleted."""
        assert 'deleted' in delete_image_result['message'].lower()

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

    def test_delete_error_returns_false(self, delete_image_error_result):
        """Test that ClientError returns success=False."""
        assert delete_image_error_result['success'] is False

    def test_delete_error_includes_error(self, delete_image_error_result):
        """Test that ClientError includes error in result."""
        assert 'error' in delete_image_error_result
