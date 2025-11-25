import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'scripts' / 'cleanup_packer_artifacts'))

from cleanup_packer_artifacts import get_snapshot_ids_for_ami


class TestGetSnapshotIdsForAmi:

    def test_returns_empty_set_for_empty_block_device_mappings(self):
        image = {'BlockDeviceMappings': []}

        result = get_snapshot_ids_for_ami(image)

        assert result == set()

    def test_returns_snapshot_id_from_ebs_block_device(self):
        image = {
            'BlockDeviceMappings': [
                {'Ebs': {'SnapshotId': 'snap-123'}}
            ]
        }

        result = get_snapshot_ids_for_ami(image)

        assert result == {'snap-123'}

    def test_returns_multiple_snapshot_ids(self):
        image = {
            'BlockDeviceMappings': [
                {'Ebs': {'SnapshotId': 'snap-123'}},
                {'Ebs': {'SnapshotId': 'snap-456'}}
            ]
        }

        result = get_snapshot_ids_for_ami(image)

        assert result == {'snap-123', 'snap-456'}

    def test_ignores_block_devices_without_ebs(self):
        image = {
            'BlockDeviceMappings': [
                {'DeviceName': '/dev/sda1'},
                {'Ebs': {'SnapshotId': 'snap-123'}}
            ]
        }

        result = get_snapshot_ids_for_ami(image)

        assert result == {'snap-123'}

    def test_ignores_ebs_without_snapshot_id(self):
        image = {
            'BlockDeviceMappings': [
                {'Ebs': {}},
                {'Ebs': {'SnapshotId': 'snap-123'}}
            ]
        }

        result = get_snapshot_ids_for_ami(image)

        assert result == {'snap-123'}

    def test_returns_empty_set_when_no_block_device_mappings_key(self):
        image = {}

        result = get_snapshot_ids_for_ami(image)

        assert result == set()
