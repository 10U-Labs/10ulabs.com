"""Unit tests for cleanup_launch_templates functionality."""

from botocore.exceptions import ClientError

TAGS = {'Purpose': 'GitHub self-hosted EC2 runner'}
EXCLUDE_TAGS: dict[str, str] = {}


class TestCleanupLaunchTemplatesReturnsDeletedCount:
    """Tests for cleanup_launch_templates return value."""

    def test_returns_zero_when_no_launch_templates(self, cleanup, mock_ec2_client):
        """Test that cleanup returns zero when no launch templates exist."""
        mock_ec2_client.describe_launch_templates.return_value = {'LaunchTemplates': []}

        result = cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert result == 0

    def test_returns_count_of_deleted_launch_templates(self, cleanup, mock_ec2_client):
        """Test that cleanup returns count of deleted launch templates."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test1'},
                {'LaunchTemplateId': 'lt-456', 'LaunchTemplateName': 'ami-builder-test2'}
            ]
        }

        result = cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert result == 2


class TestCleanupLaunchTemplatesCallsDeleteLaunchTemplate:
    """Tests for cleanup_launch_templates delete operations."""

    def test_calls_delete_launch_template_for_each_id(self, cleanup, mock_ec2_client):
        """Test that delete_launch_template is called for each template id."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test'}
            ]
        }

        cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        mock_ec2_client.delete_launch_template.assert_called_once_with(LaunchTemplateId='lt-123')

    def test_calls_delete_for_multiple_launch_templates(self, cleanup, mock_ec2_client):
        """Test that delete is called for multiple launch templates."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test1'},
                {'LaunchTemplateId': 'lt-456', 'LaunchTemplateName': 'ami-builder-test2'}
            ]
        }

        cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert mock_ec2_client.delete_launch_template.call_count == 2


class TestCleanupLaunchTemplatesDryRun:
    """Tests for cleanup_launch_templates dry run mode."""

    def test_dry_run_does_not_delete(self, cleanup, mock_ec2_client):
        """Test that dry run does not delete launch templates."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test'}
            ]
        }

        cleanup.cleanup_launch_templates(mock_ec2_client, True, TAGS, EXCLUDE_TAGS)

        mock_ec2_client.delete_launch_template.assert_not_called()

    def test_dry_run_still_returns_count(self, cleanup, mock_ec2_client):
        """Test that dry run still returns count of launch templates."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test1'},
                {'LaunchTemplateId': 'lt-456', 'LaunchTemplateName': 'ami-builder-test2'}
            ]
        }

        result = cleanup.cleanup_launch_templates(mock_ec2_client, True, TAGS, EXCLUDE_TAGS)

        assert result == 2

    def test_continues_on_client_error(self, cleanup, mock_ec2_client):
        """Test that cleanup continues when client error occurs."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'ami-builder-test1'},
                {'LaunchTemplateId': 'lt-456', 'LaunchTemplateName': 'ami-builder-test2'}
            ]
        }
        mock_ec2_client.delete_launch_template.side_effect = [
            ClientError(
                {'Error': {'Code': 'LaunchTemplateIdDoesNotExist'}},
                'delete_launch_template'
            ),
            None
        ]

        result = cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        assert result == 1


class TestCleanupLaunchTemplatesFiltersByTag:
    """Tests for cleanup_launch_templates tag filtering."""

    def test_filters_by_tag_key_and_value(self, cleanup, mock_ec2_client):
        """Test that cleanup filters by tag key and value."""
        mock_ec2_client.describe_launch_templates.return_value = {'LaunchTemplates': []}

        cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        mock_ec2_client.describe_launch_templates.assert_called_once()
        call_args = mock_ec2_client.describe_launch_templates.call_args
        filters = call_args[1]['Filters']
        tag_filter = filters[0]
        assert tag_filter['Name'] == 'tag:Purpose'
        assert tag_filter['Values'] == ['GitHub self-hosted EC2 runner']

    def test_uses_filters_keyword_argument(self, cleanup, mock_ec2_client):
        """Test that cleanup uses Filters keyword argument."""
        mock_ec2_client.describe_launch_templates.return_value = {'LaunchTemplates': []}

        cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS, EXCLUDE_TAGS)

        call_args = mock_ec2_client.describe_launch_templates.call_args
        assert 'Filters' in call_args[1]


class TestCleanupLaunchTemplatesExcludeTags:
    """Tests for cleanup_launch_templates exclude tags functionality."""

    def test_skips_launch_template_with_excluded_tag(self, cleanup, mock_ec2_client):
        """Test that cleanup skips launch template with excluded tag."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [{
                'LaunchTemplateId': 'lt-123',
                'LaunchTemplateName': 'protected-lt',
                'Tags': [{'Key': 'ManagedBy', 'Value': 'terraform'}]
            }]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS, exclude_tags)

        assert result == 0

    def test_does_not_delete_launch_template_with_excluded_tag(self, cleanup, mock_ec2_client):
        """Test that cleanup does not delete launch template with excluded tag."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [{
                'LaunchTemplateId': 'lt-123',
                'LaunchTemplateName': 'protected-lt',
                'Tags': [{'Key': 'ManagedBy', 'Value': 'terraform'}]
            }]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS, exclude_tags)

        mock_ec2_client.delete_launch_template.assert_not_called()

    def test_deletes_launch_template_without_excluded_tag(self, cleanup, mock_ec2_client):
        """Test that cleanup deletes launch template without excluded tag."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [{
                'LaunchTemplateId': 'lt-123',
                'LaunchTemplateName': 'ephemeral-lt',
                'Tags': [{'Key': 'Purpose', 'Value': 'runner'}]
            }]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS, exclude_tags)

        assert result == 1

    def test_deletes_only_non_protected_launch_templates(self, cleanup, mock_ec2_client):
        """Test that cleanup deletes only non-protected launch templates."""
        mock_ec2_client.describe_launch_templates.return_value = {
            'LaunchTemplates': [
                {
                    'LaunchTemplateId': 'lt-123',
                    'LaunchTemplateName': 'protected-lt',
                    'Tags': [{'Key': 'ManagedBy', 'Value': 'terraform'}]
                },
                {
                    'LaunchTemplateId': 'lt-456',
                    'LaunchTemplateName': 'ephemeral-lt',
                    'Tags': [{'Key': 'Purpose', 'Value': 'runner'}]
                }
            ]
        }
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.cleanup_launch_templates(mock_ec2_client, False, TAGS, exclude_tags)

        assert result == 1
