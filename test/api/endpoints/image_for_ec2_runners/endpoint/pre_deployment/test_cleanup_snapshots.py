"""Unit tests for cleanup_snapshots functionality."""


class TestCleanupSnapshotsReturnsDeletedCount:
    """Tests for cleanup_snapshots return value."""

    def test_returns_zero_when_no_snapshots(self, cleanup, mock_ec2_client):
        """Test that cleanup returns zero when no snapshots exist."""
        result = cleanup.cleanup_snapshots(mock_ec2_client, set(), False)

        assert result == 0

    def test_returns_count_of_deleted_snapshots(self, cleanup, mock_ec2_client):
        """Test that cleanup returns count of deleted snapshots."""
        result = cleanup.cleanup_snapshots(mock_ec2_client, {'snap-123', 'snap-456'}, False)

        assert result == 2


class TestCleanupSnapshotsCallsDeleteSnapshot:
    """Tests for cleanup_snapshots delete operations."""

    def test_calls_delete_snapshot_for_each_id(self, cleanup, mock_ec2_client):
        """Test that delete_snapshot is called for each snapshot id."""
        cleanup.cleanup_snapshots(mock_ec2_client, {'snap-123'}, False)

        mock_ec2_client.delete_snapshot.assert_called_once_with(SnapshotId='snap-123')

    def test_calls_delete_snapshot_for_multiple_ids(self, cleanup, mock_ec2_client):
        """Test that delete_snapshot is called for multiple snapshot ids."""
        cleanup.cleanup_snapshots(mock_ec2_client, {'snap-123', 'snap-456'}, False)

        assert mock_ec2_client.delete_snapshot.call_count == 2


class TestCleanupSnapshotsDryRun:
    """Tests for cleanup_snapshots dry run mode."""

    def test_dry_run_does_not_delete(self, cleanup, mock_ec2_client):
        """Test that dry run does not delete snapshots."""
        cleanup.cleanup_snapshots(mock_ec2_client, {'snap-123'}, True)

        mock_ec2_client.delete_snapshot.assert_not_called()

    def test_dry_run_still_returns_count(self, cleanup, mock_ec2_client):
        """Test that dry run still returns count of snapshots."""
        result = cleanup.cleanup_snapshots(mock_ec2_client, {'snap-123', 'snap-456'}, True)

        assert result == 2
