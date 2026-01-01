"""Unit tests for get_latest_ami_id functionality."""

from unittest.mock import MagicMock
from botocore.exceptions import ClientError


class TestGetLatestAmiIdSuccess:
    """Tests for get_latest_ami_id when successful."""

    def test_returns_ami_id_from_ec2(self, cleanup):
        """Test that AMI ID is returned from EC2 query."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-12345678',
                'CreationDate': '2024-01-01T00:00:00.000Z'
            }]
        }

        result = cleanup.get_latest_ami_id(
            mock_ec2, 'Purpose', 'GitHub self-hosted EC2 runner', 'Stable', 'true'
        )

        assert result == 'ami-12345678'

    def test_calls_ec2_with_self_owner(self, cleanup):
        """Test that EC2 is called with self owner filter."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-12345678',
                'CreationDate': '2024-01-01T00:00:00.000Z'
            }]
        }

        cleanup.get_latest_ami_id(
            mock_ec2, 'Purpose', 'GitHub self-hosted EC2 runner', 'Stable', 'true'
        )

        call_kwargs = mock_ec2.describe_images.call_args[1]
        assert call_kwargs['Owners'] == ['self']

    def test_calls_ec2_with_purpose_tag_filter(self, cleanup):
        """Test that EC2 is called with purpose tag filter."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-12345678',
                'CreationDate': '2024-01-01T00:00:00.000Z'
            }]
        }

        cleanup.get_latest_ami_id(
            mock_ec2, 'Purpose', 'GitHub self-hosted EC2 runner', 'Stable', 'true'
        )

        call_kwargs = mock_ec2.describe_images.call_args[1]
        filter_names = [f['Name'] for f in call_kwargs['Filters']]
        assert 'tag:Purpose' in filter_names

    def test_calls_ec2_with_stable_tag_filter(self, cleanup):
        """Test that EC2 is called with stable tag filter."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-12345678',
                'CreationDate': '2024-01-01T00:00:00.000Z'
            }]
        }

        cleanup.get_latest_ami_id(
            mock_ec2, 'Purpose', 'GitHub self-hosted EC2 runner', 'Stable', 'true'
        )

        call_kwargs = mock_ec2.describe_images.call_args[1]
        filter_names = [f['Name'] for f in call_kwargs['Filters']]
        assert 'tag:Stable' in filter_names

    def test_calls_ec2_with_state_filter(self, cleanup):
        """Test that EC2 is called with state filter."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-12345678',
                'CreationDate': '2024-01-01T00:00:00.000Z'
            }]
        }

        cleanup.get_latest_ami_id(
            mock_ec2, 'Purpose', 'GitHub self-hosted EC2 runner', 'Stable', 'true'
        )

        call_kwargs = mock_ec2.describe_images.call_args[1]
        filter_names = [f['Name'] for f in call_kwargs['Filters']]
        assert 'state' in filter_names

    def test_returns_most_recent_ami(self, cleanup):
        """Test that the most recent AMI is returned when multiple exist."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-older',
                    'CreationDate': '2024-01-01T00:00:00.000Z'
                },
                {
                    'ImageId': 'ami-newest',
                    'CreationDate': '2024-06-01T00:00:00.000Z'
                },
                {
                    'ImageId': 'ami-middle',
                    'CreationDate': '2024-03-01T00:00:00.000Z'
                }
            ]
        }

        result = cleanup.get_latest_ami_id(
            mock_ec2, 'Purpose', 'GitHub self-hosted EC2 runner', 'Stable', 'true'
        )

        assert result == 'ami-newest'


class TestGetLatestAmiIdNoImages:
    """Tests for get_latest_ami_id when no images found."""

    def test_returns_none_when_no_images(self, cleanup):
        """Test that None is returned when no images match."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_images.return_value = {'Images': []}

        result = cleanup.get_latest_ami_id(
            mock_ec2, 'Purpose', 'GitHub self-hosted EC2 runner', 'Stable', 'true'
        )

        assert result is None


class TestGetLatestAmiIdClientErrors:
    """Tests for get_latest_ami_id when client errors occur."""

    def test_returns_none_on_access_denied_error(self, cleanup):
        """Test that None is returned on access denied error."""
        mock_ec2 = MagicMock()
        mock_ec2.describe_images.side_effect = ClientError(
            {
                'Error': {
                    'Code': 'AccessDenied',
                    'Message': 'Access denied',
                }
            },
            'DescribeImages',
        )

        result = cleanup.get_latest_ami_id(
            mock_ec2, 'Purpose', 'GitHub self-hosted EC2 runner', 'Stable', 'true'
        )

        assert result is None
