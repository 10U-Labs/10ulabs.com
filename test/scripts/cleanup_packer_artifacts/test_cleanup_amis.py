import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'scripts' / 'cleanup_packer_artifacts'))

from cleanup_packer_artifacts import cleanup_amis


class TestCleanupAmisReturnsDeletedCount:

    def test_returns_zero_when_no_amis(self, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {'Images': []}

        count, snapshots = cleanup_amis(mock_ec2_client, 'ami-latest', set(), False, True)

        assert count == 0

    def test_returns_count_of_deregistered_amis(self, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {'ImageId': 'ami-123', 'Name': 'test-ami', 'BlockDeviceMappings': []},
                {'ImageId': 'ami-456', 'Name': 'test-ami-2', 'BlockDeviceMappings': []}
            ]
        }

        count, snapshots = cleanup_amis(mock_ec2_client, 'ami-latest', set(), False, True)

        assert count == 2


class TestCleanupAmisSkipsLatestAmi:

    def test_skips_latest_ami(self, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {'ImageId': 'ami-latest', 'Name': 'latest-ami', 'BlockDeviceMappings': []},
                {'ImageId': 'ami-old', 'Name': 'old-ami', 'BlockDeviceMappings': []}
            ]
        }

        count, snapshots = cleanup_amis(mock_ec2_client, 'ami-latest', set(), False, True)

        assert count == 1

    def test_does_not_deregister_latest_ami(self, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {'ImageId': 'ami-latest', 'Name': 'latest-ami', 'BlockDeviceMappings': []}
            ]
        }

        cleanup_amis(mock_ec2_client, 'ami-latest', set(), False, True)

        mock_ec2_client.deregister_image.assert_not_called()


class TestCleanupAmisCollectsSnapshots:

    def test_collects_snapshot_ids_from_deregistered_amis(self, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-123',
                    'Name': 'test-ami',
                    'BlockDeviceMappings': [{'Ebs': {'SnapshotId': 'snap-123'}}]
                }
            ]
        }

        count, snapshots = cleanup_amis(mock_ec2_client, 'ami-latest', set(), False, True)

        assert snapshots == {'snap-123'}

    def test_excludes_protected_snapshots(self, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-123',
                    'Name': 'test-ami',
                    'BlockDeviceMappings': [
                        {'Ebs': {'SnapshotId': 'snap-123'}},
                        {'Ebs': {'SnapshotId': 'snap-protected'}}
                    ]
                }
            ]
        }

        count, snapshots = cleanup_amis(mock_ec2_client, 'ami-latest', {'snap-protected'}, False, True)

        assert snapshots == {'snap-123'}

    def test_returns_empty_snapshots_when_cleanup_disabled(self, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-123',
                    'Name': 'test-ami',
                    'BlockDeviceMappings': [{'Ebs': {'SnapshotId': 'snap-123'}}]
                }
            ]
        }

        count, snapshots = cleanup_amis(mock_ec2_client, 'ami-latest', set(), False, False)

        assert snapshots == set()


class TestCleanupAmisDryRun:

    def test_dry_run_does_not_deregister(self, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {'ImageId': 'ami-123', 'Name': 'test-ami', 'BlockDeviceMappings': []}
            ]
        }

        cleanup_amis(mock_ec2_client, 'ami-latest', set(), True, True)

        mock_ec2_client.deregister_image.assert_not_called()

    def test_dry_run_still_returns_count(self, mock_ec2_client):
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {'ImageId': 'ami-123', 'Name': 'test-ami', 'BlockDeviceMappings': []}
            ]
        }

        count, snapshots = cleanup_amis(mock_ec2_client, 'ami-latest', set(), True, True)

        assert count == 1
