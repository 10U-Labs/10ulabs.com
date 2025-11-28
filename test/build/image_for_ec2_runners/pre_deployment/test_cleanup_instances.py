from botocore.exceptions import ClientError

TAGS = {'Purpose': 'GitHub self-hosted EC2 runner'}
EXCLUDE_TAGS: dict[str, str] = {}


class TestCleanupInstancesReturnsDeletedCount:

    def test_returns_zero_when_no_instances(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {'Reservations': []}

        result = cleanup.cleanup_instances(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert result == 0

    def test_returns_count_of_terminated_instances(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [
                    {'InstanceId': 'i-123'},
                    {'InstanceId': 'i-456'}
                ]
            }]
        }

        result = cleanup.cleanup_instances(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert result == 2

    def test_handles_multiple_reservations(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [
                {'Instances': [{'InstanceId': 'i-123'}]},
                {'Instances': [{'InstanceId': 'i-456'}]}
            ]
        }

        result = cleanup.cleanup_instances(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert result == 2


class TestCleanupInstancesCallsTerminateInstances:

    def test_calls_terminate_instances_for_each_id(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{'Instances': [{'InstanceId': 'i-123'}]}]
        }

        cleanup.cleanup_instances(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        mock_ec2_client.terminate_instances.assert_called_once_with(InstanceIds=['i-123'])

    def test_calls_terminate_for_multiple_instances(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [
                    {'InstanceId': 'i-123'},
                    {'InstanceId': 'i-456'}
                ]
            }]
        }

        cleanup.cleanup_instances(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert mock_ec2_client.terminate_instances.call_count == 2

    def test_continues_on_client_error(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [
                    {'InstanceId': 'i-123'},
                    {'InstanceId': 'i-456'}
                ]
            }]
        }
        mock_ec2_client.terminate_instances.side_effect = [
            ClientError({'Error': {'Code': 'InvalidInstanceID.NotFound'}}, 'terminate_instances'),
            None
        ]

        result = cleanup.cleanup_instances(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert result == 1


class TestCleanupInstancesDryRun:

    def test_dry_run_does_not_terminate(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{'Instances': [{'InstanceId': 'i-123'}]}]
        }

        cleanup.cleanup_instances(mock_ec2_client, True, TAGS, EXCLUDE_TAGS)

        mock_ec2_client.terminate_instances.assert_not_called()

    def test_dry_run_still_returns_count(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [
                    {'InstanceId': 'i-123'},
                    {'InstanceId': 'i-456'}
                ]
            }]
        }

        result = cleanup.cleanup_instances(mock_ec2_client, True, TAGS, EXCLUDE_TAGS)

        assert result == 2


class TestCleanupInstancesFiltersByTag:

    def test_filters_by_tag_key_and_value(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {'Reservations': []}

        cleanup.cleanup_instances(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        mock_ec2_client.describe_instances.assert_called_once()
        call_args = mock_ec2_client.describe_instances.call_args
        filters = call_args[1]['Filters']
        tag_filter = next(f for f in filters if f['Name'] == 'tag:Purpose')
        assert tag_filter['Values'] == ['GitHub self-hosted EC2 runner']

    def test_filters_by_instance_state(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {'Reservations': []}

        cleanup.cleanup_instances(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        call_args = mock_ec2_client.describe_instances.call_args
        filters = call_args[1]['Filters']
        state_filter = next(f for f in filters if f['Name'] == 'instance-state-name')
        assert state_filter['Values'] == ['running', 'stopped', 'stopping', 'pending']


class TestCleanupInstancesExcludeTags:

    def test_skips_instance_with_excluded_tag(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{
                    'InstanceId': 'i-123',
                    'Tags': [{'Key': 'ManagedBy', 'Value': 'terraform'}]
                }]
            }]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.cleanup_instances(mock_ec2_client, False, TAGS, exclude_tags)

        assert result == 0

    def test_does_not_terminate_instance_with_excluded_tag(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{
                    'InstanceId': 'i-123',
                    'Tags': [{'Key': 'ManagedBy', 'Value': 'terraform'}]
                }]
            }]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        cleanup.cleanup_instances(mock_ec2_client, False, TAGS, exclude_tags)

        mock_ec2_client.terminate_instances.assert_not_called()

    def test_terminates_instance_without_excluded_tag(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{
                    'InstanceId': 'i-123',
                    'Tags': [{'Key': 'Purpose', 'Value': 'runner'}]
                }]
            }]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.cleanup_instances(mock_ec2_client, False, TAGS, exclude_tags)

        assert result == 1

    def test_terminates_only_non_protected_instances(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [
                    {
                        'InstanceId': 'i-123',
                        'Tags': [{'Key': 'ManagedBy', 'Value': 'terraform'}]
                    },
                    {
                        'InstanceId': 'i-456',
                        'Tags': [{'Key': 'Purpose', 'Value': 'runner'}]
                    }
                ]
            }]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.cleanup_instances(mock_ec2_client, False, TAGS, exclude_tags)

        assert result == 1
