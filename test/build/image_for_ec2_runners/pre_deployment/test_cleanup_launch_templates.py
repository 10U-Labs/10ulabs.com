from botocore.exceptions import ClientError


class TestCleanupLaunchTemplatesReturnsDeletedCount:

    def test_returns_zero_when_no_launch_templates(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {'LaunchTemplates': []}

        result = cleanup.cleanup_launch_templates(mock_ec2_client, False)

        assert result == 0

    def test_returns_count_of_deleted_launch_templates(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test1'},
                {'LaunchTemplateId': 'lt-456', 'LaunchTemplateName': 'ami-builder-test2'}
            ]
        }

        result = cleanup.cleanup_launch_templates(mock_ec2_client, False)

        assert result == 2


class TestCleanupLaunchTemplatesCallsDeleteLaunchTemplate:

    def test_calls_delete_launch_template_for_each_id(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test'}
            ]
        }

        cleanup.cleanup_launch_templates(mock_ec2_client, False)

        mock_ec2_client.delete_launch_template.assert_called_once_with(LaunchTemplateId='lt-123')

    def test_calls_delete_for_multiple_launch_templates(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test1'},
                {'LaunchTemplateId': 'lt-456', 'LaunchTemplateName': 'ami-builder-test2'}
            ]
        }

        cleanup.cleanup_launch_templates(mock_ec2_client, False)

        assert mock_ec2_client.delete_launch_template.call_count == 2


class TestCleanupLaunchTemplatesDryRun:

    def test_dry_run_does_not_delete(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test'}
            ]
        }

        cleanup.cleanup_launch_templates(mock_ec2_client, True)

        mock_ec2_client.delete_launch_template.assert_not_called()

    def test_dry_run_still_returns_count(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test1'},
                {'LaunchTemplateId': 'lt-456', 'LaunchTemplateName': 'ami-builder-test2'}
            ]
        }

        result = cleanup.cleanup_launch_templates(mock_ec2_client, True)

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

        result = cleanup.cleanup_launch_templates(mock_ec2_client, False)

        assert result == 1
