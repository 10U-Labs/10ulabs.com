"""Unit tests for AMI cleanup operations.

Tests for find_amis_by_name_prefix and cleanup_amis error handling.
"""
from unittest.mock import MagicMock
import pytest
from botocore.exceptions import ClientError


class TestFindAmisByNamePrefix:
    """Tests for find_amis_by_name_prefix function."""

    def test_returns_empty_dict_when_no_prefix(self, cleanup, mock_ec2_client):
        """Verify returns empty dict when prefix is empty."""
        result = cleanup.find_amis_by_name_prefix(mock_ec2_client, "")
        assert result == {}
        mock_ec2_client.describe_images.assert_not_called()

    def test_returns_empty_dict_when_prefix_is_none(self, cleanup, mock_ec2_client):
        """Verify returns empty dict when prefix is None."""
        result = cleanup.find_amis_by_name_prefix(mock_ec2_client, None)
        assert result == {}

    def test_finds_amis_with_matching_prefix(self, cleanup, mock_ec2_client):
        """Verify finds AMIs matching the name prefix."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {'ImageId': 'ami-1', 'Name': 'github-runner-v1'},
                {'ImageId': 'ami-2', 'Name': 'github-runner-v2'},
            ]
        }

        result = cleanup.find_amis_by_name_prefix(mock_ec2_client, "github-runner")

        assert 'ami-1' in result
        assert 'ami-2' in result
        mock_ec2_client.describe_images.assert_called_once()
        call_args = mock_ec2_client.describe_images.call_args
        filters = call_args[1]['Filters']
        name_filter = [f for f in filters if f['Name'] == 'name'][0]
        assert name_filter['Values'] == ['github-runner*']

    def test_handles_describe_error(self, cleanup, mock_ec2_client):
        """Verify handles describe_images error gracefully."""
        mock_ec2_client.describe_images.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'DescribeImages'
        )

        result = cleanup.find_amis_by_name_prefix(mock_ec2_client, "github-runner")

        assert result == {}


class TestCleanupAmisDeregisterError:
    """Tests for cleanup_amis error handling when deregister fails."""

    def test_handles_deregister_error_gracefully(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Verify handles deregister_image error and continues."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-fail',
                    'Name': 'will-fail',
                    'BlockDeviceMappings': []
                },
                {
                    'ImageId': 'ami-success',
                    'Name': 'will-succeed',
                    'BlockDeviceMappings': []
                },
            ]
        }
        # First call fails, second succeeds
        mock_ec2_client.deregister_image.side_effect = [
            ClientError(
                {'Error': {'Code': 'InvalidAMIID.Unavailable', 'Message': 'AMI unavailable'}},
                'DeregisterImage'
            ),
            {}
        ]

        params = make_ami_cleanup_params(
            cleanup,
            latest_ami_id='ami-latest',
            tags={'Purpose': 'test'},
            dry_run=False
        )
        deleted_count, _ = cleanup.cleanup_amis(mock_ec2_client, params)

        # Only 1 succeeded, 1 failed
        assert deleted_count == 1

    def test_counts_only_successful_deregistrations(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Verify counts only successful deregistrations."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-error',
                'Name': 'error-ami',
                'BlockDeviceMappings': []
            }]
        }
        mock_ec2_client.deregister_image.side_effect = ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Access denied'}},
            'DeregisterImage'
        )

        params = make_ami_cleanup_params(
            cleanup,
            latest_ami_id='ami-latest',
            tags={'Purpose': 'test'},
            dry_run=False
        )
        deleted_count, _ = cleanup.cleanup_amis(mock_ec2_client, params)

        assert deleted_count == 0


class TestCleanupAmisWithNamePrefix:
    """Tests for cleanup_amis with ami_name_prefix."""

    def test_cleans_up_amis_by_name_prefix(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Verify cleans up AMIs matching name prefix."""
        # First call for tags returns empty, second for prefix returns AMIs
        mock_ec2_client.describe_images.side_effect = [
            {'Images': []},  # find_amis_by_tags
            {'Images': [{    # find_amis_by_name_prefix
                'ImageId': 'ami-prefix',
                'Name': 'runner-ami-v1',
                'BlockDeviceMappings': []
            }]},
        ]
        mock_ec2_client.deregister_image.return_value = {}

        params = make_ami_cleanup_params(
            cleanup,
            latest_ami_id='ami-latest',
            tags={'Purpose': 'test'},
            ami_name_prefix='runner-ami',
            dry_run=False
        )
        deleted_count, _ = cleanup.cleanup_amis(mock_ec2_client, params)

        assert deleted_count == 1
        mock_ec2_client.deregister_image.assert_called_once_with(ImageId='ami-prefix')
