"""Unit tests for get_latest_snapshot_ids functionality."""
from botocore.exceptions import ClientError


class TestGetLatestSnapshotIdsWithValidAmi:
    """Tests for get_latest_snapshot_ids when AMI exists."""

    def test_returns_snapshot_id_from_ami(self, cleanup, mock_ec2_client):
        """Test that snapshot ID is returned from a valid AMI."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [{
                'BlockDeviceMappings': [{'Ebs': {'SnapshotId': 'snap-123'}}]
            }]
        }

        result = cleanup.get_latest_snapshot_ids(mock_ec2_client, 'ami-123')

        assert result == {'snap-123'}

    def test_returns_multiple_snapshot_ids(self, cleanup, mock_ec2_client):
        """Test that multiple snapshot IDs are returned from an AMI."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [{
                'BlockDeviceMappings': [
                    {'Ebs': {'SnapshotId': 'snap-123'}},
                    {'Ebs': {'SnapshotId': 'snap-456'}}
                ]
            }]
        }

        result = cleanup.get_latest_snapshot_ids(mock_ec2_client, 'ami-123')

        assert result == {'snap-123', 'snap-456'}


class TestGetLatestSnapshotIdsWithNoAmi:
    """Tests for get_latest_snapshot_ids when no AMI is provided."""

    def test_returns_empty_set_when_ami_id_is_none(self, cleanup, mock_ec2_client):
        """Test that empty set is returned when AMI ID is None."""
        result = cleanup.get_latest_snapshot_ids(mock_ec2_client, None)

        assert result == set()

    def test_does_not_call_describe_images_when_ami_id_is_none(self, cleanup, mock_ec2_client):
        """Test that describe_images is not called when AMI ID is None."""
        cleanup.get_latest_snapshot_ids(mock_ec2_client, None)

        mock_ec2_client.describe_images.assert_not_called()
        assert True  # Explicit pass


class TestGetLatestSnapshotIdsWithEmptyResponse:
    """Tests for get_latest_snapshot_ids when no images or snapshots are found."""

    def test_returns_empty_set_when_no_images_found(self, cleanup, mock_ec2_client):
        """Test that empty set is returned when no images are found."""
        mock_ec2_client.describe_images.return_value = {'Images': []}

        result = cleanup.get_latest_snapshot_ids(mock_ec2_client, 'ami-123')

        assert result == set()

    def test_returns_empty_set_when_no_block_devices(self, cleanup, mock_ec2_client):
        """Test that empty set is returned when AMI has no block devices."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [{'BlockDeviceMappings': []}]
        }

        result = cleanup.get_latest_snapshot_ids(mock_ec2_client, 'ami-123')

        assert result == set()

    def test_returns_empty_set_on_client_error(self, cleanup, mock_ec2_client):
        """Test that empty set is returned when a client error occurs."""
        mock_ec2_client.describe_images.side_effect = ClientError(
            {'Error': {'Code': 'InvalidAMIID.NotFound'}}, 'describe_images'
        )

        result = cleanup.get_latest_snapshot_ids(mock_ec2_client, 'ami-123')

        assert result == set()
