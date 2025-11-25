class TestGetSnapshotIdsForAmi:

    def test_returns_empty_set_for_empty_block_device_mappings(self, cleanup_packer_artifacts):
        image = {'BlockDeviceMappings': []}

        result = cleanup_packer_artifacts.get_snapshot_ids_for_ami(image)

        assert result == set()

    def test_returns_snapshot_id_from_ebs_block_device(self, cleanup_packer_artifacts):
        image = {
            'BlockDeviceMappings': [
                {'Ebs': {'SnapshotId': 'snap-123'}}
            ]
        }

        result = cleanup_packer_artifacts.get_snapshot_ids_for_ami(image)

        assert result == {'snap-123'}

    def test_returns_multiple_snapshot_ids(self, cleanup_packer_artifacts):
        image = {
            'BlockDeviceMappings': [
                {'Ebs': {'SnapshotId': 'snap-123'}},
                {'Ebs': {'SnapshotId': 'snap-456'}}
            ]
        }

        result = cleanup_packer_artifacts.get_snapshot_ids_for_ami(image)

        assert result == {'snap-123', 'snap-456'}

    def test_ignores_block_devices_without_ebs(self, cleanup_packer_artifacts):
        image = {
            'BlockDeviceMappings': [
                {'DeviceName': '/dev/sda1'},
                {'Ebs': {'SnapshotId': 'snap-123'}}
            ]
        }

        result = cleanup_packer_artifacts.get_snapshot_ids_for_ami(image)

        assert result == {'snap-123'}

    def test_ignores_ebs_without_snapshot_id(self, cleanup_packer_artifacts):
        image = {
            'BlockDeviceMappings': [
                {'Ebs': {}},
                {'Ebs': {'SnapshotId': 'snap-123'}}
            ]
        }

        result = cleanup_packer_artifacts.get_snapshot_ids_for_ami(image)

        assert result == {'snap-123'}

    def test_returns_empty_set_when_no_block_device_mappings_key(self, cleanup_packer_artifacts):
        image = {}

        result = cleanup_packer_artifacts.get_snapshot_ids_for_ami(image)

        assert result == set()
