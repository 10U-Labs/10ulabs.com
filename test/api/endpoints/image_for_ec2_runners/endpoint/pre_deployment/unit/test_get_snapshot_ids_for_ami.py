"""Unit tests for get_snapshot_ids_for_ami functionality."""


class TestGetSnapshotIdsForAmi:
    """Tests for get_snapshot_ids_for_ami when extracting snapshot IDs from AMI details."""

    def test_returns_empty_set_for_empty_block_device_mappings(self, cleanup):
        """Test that empty set is returned for empty block device mappings."""
        image = {'BlockDeviceMappings': []}

        result = cleanup.get_snapshot_ids_for_ami(image)

        assert result == set()

    def test_returns_snapshot_id_from_ebs_block_device(self, cleanup):
        """Test that snapshot ID is extracted from EBS block device."""
        image = {
            'BlockDeviceMappings': [
                {'Ebs': {'SnapshotId': 'snap-123'}}
            ]
        }

        result = cleanup.get_snapshot_ids_for_ami(image)

        assert result == {'snap-123'}

    def test_returns_multiple_snapshot_ids(self, cleanup):
        """Test that multiple snapshot IDs are extracted from block devices."""
        image = {
            'BlockDeviceMappings': [
                {'Ebs': {'SnapshotId': 'snap-123'}},
                {'Ebs': {'SnapshotId': 'snap-456'}}
            ]
        }

        result = cleanup.get_snapshot_ids_for_ami(image)

        assert result == {'snap-123', 'snap-456'}

    def test_ignores_block_devices_without_ebs(self, cleanup):
        """Test that block devices without EBS are ignored."""
        image = {
            'BlockDeviceMappings': [
                {'DeviceName': '/dev/sda1'},
                {'Ebs': {'SnapshotId': 'snap-123'}}
            ]
        }

        result = cleanup.get_snapshot_ids_for_ami(image)

        assert result == {'snap-123'}

    def test_ignores_ebs_without_snapshot_id(self, cleanup):
        """Test that EBS volumes without snapshot ID are ignored."""
        image = {
            'BlockDeviceMappings': [
                {'Ebs': {}},
                {'Ebs': {'SnapshotId': 'snap-123'}}
            ]
        }

        result = cleanup.get_snapshot_ids_for_ami(image)

        assert result == {'snap-123'}

    def test_returns_empty_set_when_no_block_device_mappings_key(self, cleanup):
        """Test that empty set is returned when BlockDeviceMappings key is missing."""
        image = {}

        result = cleanup.get_snapshot_ids_for_ami(image)

        assert result == set()
