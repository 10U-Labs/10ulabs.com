from botocore.exceptions import ClientError

TAGS = {'Purpose': 'GitHub self-hosted EC2 runner'}


class TestCleanupLaunchTemplatesReturnsDeletedCount:

    def test_returns_zero_when_no_launch_templates(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {'LaunchTemplates': []}

        result = cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS)

        assert result == 0

    def test_returns_count_of_deleted_launch_templates(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test1'},
                {'LaunchTemplateId': 'lt-456', 'LaunchTemplateName': 'ami-builder-test2'}
            ]
        }

        result = cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS)

        assert result == 2


class TestCleanupLaunchTemplatesCallsDeleteLaunchTemplate:

    def test_calls_delete_launch_template_for_each_id(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test'}
            ]
        }

        cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS)

        mock_ec2_client.delete_launch_template.assert_called_once_with(LaunchTemplateId='lt-123')

    def test_calls_delete_for_multiple_launch_templates(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test1'},
                {'LaunchTemplateId': 'lt-456', 'LaunchTemplateName': 'ami-builder-test2'}
            ]
        }

        cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS)

        assert mock_ec2_client.delete_launch_template.call_count == 2


class TestCleanupLaunchTemplatesDryRun:

    def test_dry_run_does_not_delete(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test'}
            ]
        }

        cleanup.cleanup_launch_templates(mock_ec2_client, True, TAGS)

        mock_ec2_client.delete_launch_template.assert_not_called()

    def test_dry_run_still_returns_count(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test1'},
                {'LaunchTemplateId': 'lt-456', 'LaunchTemplateName': 'ami-builder-test2'}
            ]
        }

        result = cleanup.cleanup_launch_templates(mock_ec2_client, True, TAGS)

        assert result == 2

    def test_continues_on_client_error(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test1'},
                {'LaunchTemplateId': 'lt-456', 'LaunchTemplateName': 'ami-builder-test2'}
            ]
        }
        mock_ec2_client.delete_launch_template.side_effect = [
            ClientError({'Error': {'Code': 'LaunchTemplateIdDoesNotExist'}}, 'delete_launch_template'),
            None
        ]

        result = cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS)

        assert result == 1


class TestCleanupLaunchTemplatesFiltersByTag:

    def test_filters_by_tag_key_and_value(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {'LaunchTemplates': []}

        cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS)

        mock_ec2_client.describe_launch_templates.assert_called_once()
        call_args = mock_ec2_client.describe_launch_templates.call_args
        filters = call_args[1]['Filters']
        tag_filter = filters[0]
        assert tag_filter['Name'] == 'tag:Purpose'
        assert tag_filter['Values'] == ['GitHub self-hosted EC2 runner']

    def test_uses_filters_keyword_argument(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {'LaunchTemplates': []}

        cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS)

        call_args = mock_ec2_client.describe_launch_templates.call_args
        assert 'Filters' in call_args[1]
