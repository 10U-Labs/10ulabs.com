"""Unit tests for cleanup_amis functionality."""


class TestCleanupAmisReturnsDeletedCount:
    """Tests for cleanup_amis return value for deleted count."""

    def test_returns_zero_when_no_amis(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that zero is returned when no AMIs exist."""
        mock_ec2_client.describe_images.return_value = {'Images': []}

        count, _ = cleanup.cleanup_amis(
            mock_ec2_client, make_ami_cleanup_params(cleanup)
        )

        assert count == 0

    def test_returns_count_of_deregistered_amis(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that count of deregistered AMIs is returned."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-123',
                    'Name': 'test-ami',
                    'BlockDeviceMappings': [],
                },
                {
                    'ImageId': 'ami-456',
                    'Name': 'test-ami-2',
                    'BlockDeviceMappings': [],
                },
            ]
        }

        count, _ = cleanup.cleanup_amis(
            mock_ec2_client, make_ami_cleanup_params(cleanup)
        )

        assert count == 2


class TestCleanupAmisSkipsLatestAmi:
    """Tests for cleanup_amis skipping latest AMI."""

    def test_skips_latest_ami(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that latest AMI is skipped."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-latest',
                    'Name': 'latest-ami',
                    'BlockDeviceMappings': [],
                },
                {
                    'ImageId': 'ami-old',
                    'Name': 'old-ami',
                    'BlockDeviceMappings': [],
                },
            ]
        }

        count, _ = cleanup.cleanup_amis(
            mock_ec2_client, make_ami_cleanup_params(cleanup)
        )

        assert count == 1

    def test_does_not_deregister_latest_ami(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that latest AMI is not deregistered."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-latest',
                    'Name': 'latest-ami',
                    'BlockDeviceMappings': [],
                }
            ]
        }

        cleanup.cleanup_amis(
            mock_ec2_client, make_ami_cleanup_params(cleanup)
        )

        mock_ec2_client.deregister_image.assert_not_called()
        assert True  # Explicit pass


class TestCleanupAmisCollectsSnapshots:
    """Tests for cleanup_amis snapshot collection."""

    def test_collects_snapshot_ids_from_deregistered_amis(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that snapshot IDs are collected from deregistered AMIs."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-123',
                    'Name': 'test-ami',
                    'BlockDeviceMappings': [
                        {'Ebs': {'SnapshotId': 'snap-123'}}
                    ],
                }
            ]
        }

        _, snapshots = cleanup.cleanup_amis(
            mock_ec2_client, make_ami_cleanup_params(cleanup)
        )

        assert snapshots == {'snap-123'}

    def test_excludes_protected_snapshots(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that protected snapshots are excluded."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-123',
                    'Name': 'test-ami',
                    'BlockDeviceMappings': [
                        {'Ebs': {'SnapshotId': 'snap-123'}},
                        {'Ebs': {'SnapshotId': 'snap-protected'}},
                    ],
                }
            ]
        }

        _, snapshots = cleanup.cleanup_amis(
            mock_ec2_client,
            make_ami_cleanup_params(
                cleanup, latest_snapshot_ids={'snap-protected'}
            ),
        )

        assert snapshots == {'snap-123'}

    def test_returns_empty_snapshots_when_cleanup_disabled(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that empty snapshots returned when cleanup disabled."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-123',
                    'Name': 'test-ami',
                    'BlockDeviceMappings': [
                        {'Ebs': {'SnapshotId': 'snap-123'}}
                    ],
                }
            ]
        }

        _, snapshots = cleanup.cleanup_amis(
            mock_ec2_client,
            make_ami_cleanup_params(cleanup, cleanup_snapshots_enabled=False),
        )

        assert snapshots == set()


class TestCleanupAmisDryRun:
    """Tests for cleanup_amis dry run mode."""

    def test_dry_run_does_not_deregister(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that dry run does not deregister AMIs."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-123',
                    'Name': 'test-ami',
                    'BlockDeviceMappings': [],
                }
            ]
        }

        cleanup.cleanup_amis(
            mock_ec2_client, make_ami_cleanup_params(cleanup, dry_run=True)
        )

        mock_ec2_client.deregister_image.assert_not_called()
        assert True  # Explicit pass

    def test_dry_run_still_returns_count(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that dry run still returns count."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-123',
                    'Name': 'test-ami',
                    'BlockDeviceMappings': [],
                }
            ]
        }

        count, _ = cleanup.cleanup_amis(
            mock_ec2_client, make_ami_cleanup_params(cleanup, dry_run=True)
        )

        assert count == 1


class TestCleanupAmisFiltersByTag:
    """Tests for cleanup_amis filtering by tag."""

    def test_filters_by_tag_key_and_value(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that AMIs are filtered by tag key and value."""
        mock_ec2_client.describe_images.return_value = {'Images': []}

        cleanup.cleanup_amis(
            mock_ec2_client,
            make_ami_cleanup_params(
                cleanup, tags={'Purpose': 'GitHub self-hosted EC2 runner'}
            ),
        )

        mock_ec2_client.describe_images.assert_called_once()
        call_args = mock_ec2_client.describe_images.call_args
        filters = call_args[1]['Filters']
        tag_filter = next(f for f in filters if f['Name'] == 'tag:Purpose')
        assert tag_filter['Values'] == ['GitHub self-hosted EC2 runner']

    def test_filters_by_state(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that AMIs are filtered by state."""
        mock_ec2_client.describe_images.return_value = {'Images': []}

        cleanup.cleanup_amis(
            mock_ec2_client, make_ami_cleanup_params(cleanup)
        )

        call_args = mock_ec2_client.describe_images.call_args
        filters = call_args[1]['Filters']
        state_filter = next(f for f in filters if f['Name'] == 'state')
        assert state_filter['Values'] == ['available', 'pending', 'failed']


class TestCleanupAmisExcludeTags:
    """Tests for cleanup_amis excluding tags."""

    def test_skips_ami_with_excluded_tag(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that AMI with excluded tag is skipped."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-123',
                    'Name': 'protected-ami',
                    'BlockDeviceMappings': [],
                    'Tags': [{'Key': 'ManagedBy', 'Value': 'terraform'}],
                }
            ]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        count, _ = cleanup.cleanup_amis(
            mock_ec2_client,
            make_ami_cleanup_params(cleanup, exclude_tags=exclude_tags),
        )

        assert count == 0

    def test_does_not_deregister_ami_with_excluded_tag(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that AMI with excluded tag is not deregistered."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-123',
                    'Name': 'protected-ami',
                    'BlockDeviceMappings': [],
                    'Tags': [{'Key': 'ManagedBy', 'Value': 'terraform'}],
                }
            ]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        cleanup.cleanup_amis(
            mock_ec2_client,
            make_ami_cleanup_params(cleanup, exclude_tags=exclude_tags),
        )

        mock_ec2_client.deregister_image.assert_not_called()
        assert True  # Explicit pass

    def test_deregisters_ami_without_excluded_tag(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that AMI without excluded tag is deregistered."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-123',
                    'Name': 'ephemeral-ami',
                    'BlockDeviceMappings': [],
                    'Tags': [{'Key': 'Purpose', 'Value': 'runner'}],
                }
            ]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        count, _ = cleanup.cleanup_amis(
            mock_ec2_client,
            make_ami_cleanup_params(cleanup, exclude_tags=exclude_tags),
        )

        assert count == 1

    def test_deregisters_only_non_protected_amis(
        self, cleanup, mock_ec2_client, make_ami_cleanup_params
    ):
        """Test that only non-protected AMIs are deregistered."""
        mock_ec2_client.describe_images.return_value = {
            'Images': [
                {
                    'ImageId': 'ami-123',
                    'Name': 'protected-ami',
                    'BlockDeviceMappings': [],
                    'Tags': [{'Key': 'ManagedBy', 'Value': 'terraform'}],
                },
                {
                    'ImageId': 'ami-456',
                    'Name': 'ephemeral-ami',
                    'BlockDeviceMappings': [],
                    'Tags': [{'Key': 'Purpose', 'Value': 'runner'}],
                },
            ]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        count, _ = cleanup.cleanup_amis(
            mock_ec2_client,
            make_ami_cleanup_params(cleanup, exclude_tags=exclude_tags),
        )

        assert count == 1
