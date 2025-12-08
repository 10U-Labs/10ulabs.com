"""Unit tests for list_amis functionality."""


class TestListAmis:
    """Tests for list_amis when retrieving AMI information."""

    def test_returns_list_with_success(self, handler_module, mock_ec2):
        """Test that AMI list is returned with success status."""
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-123',
                'Name': 'github-runner-ami',
                'CreationDate': '2024-01-01T00:00:00.000Z',
                'State': 'available',
                'Architecture': 'arm64',
                'Tags': [{'Key': 'Stable', 'Value': 'true'}]
            }]
        }

        result = handler_module.list_amis()

        assert result['success'] is True

    def test_returns_correct_ami_count(self, handler_module, mock_ec2):
        """Test that correct number of AMIs is returned."""
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-123',
                'Name': 'github-runner-ami',
                'CreationDate': '2024-01-01T00:00:00.000Z',
                'State': 'available',
                'Architecture': 'arm64',
                'Tags': [{'Key': 'Stable', 'Value': 'true'}]
            }]
        }

        result = handler_module.list_amis()

        assert len(result['amis']) == 1

    def test_returns_correct_ami_id(self, handler_module, mock_ec2):
        """Test that correct AMI ID is returned in the list."""
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-123',
                'Name': 'github-runner-ami',
                'CreationDate': '2024-01-01T00:00:00.000Z',
                'State': 'available',
                'Architecture': 'arm64',
                'Tags': [{'Key': 'Stable', 'Value': 'true'}]
            }]
        }

        result = handler_module.list_amis()

        assert result['amis'][0]['ami_id'] == 'ami-123'

    def test_handles_empty_ami_list_returns_success(self, handler_module, mock_ec2):
        """Test that success is returned when AMI list is empty."""
        mock_ec2.describe_images.return_value = {'Images': []}

        result = handler_module.list_amis()

        assert result['success'] is True

    def test_handles_empty_ami_list_returns_empty_array(self, handler_module, mock_ec2):
        """Test that empty array is returned when AMI list is empty."""
        mock_ec2.describe_images.return_value = {'Images': []}

        result = handler_module.list_amis()

        assert result['amis'] == []

    def test_handles_missing_stable_tag_returns_success(self, handler_module, mock_ec2):
        """Test that success is returned when stable tag is missing."""
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-123',
                'Name': 'github-runner-ami',
                'CreationDate': '2024-01-01T00:00:00.000Z',
                'State': 'available',
                'Architecture': 'arm64',
                'Tags': []
            }]
        }

        result = handler_module.list_amis()

        assert result['success'] is True

    def test_handles_missing_stable_tag_defaults_to_false(self, handler_module, mock_ec2):
        """Test that stable tag defaults to false when missing."""
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-123',
                'Name': 'github-runner-ami',
                'CreationDate': '2024-01-01T00:00:00.000Z',
                'State': 'available',
                'Architecture': 'arm64',
                'Tags': []
            }]
        }

        result = handler_module.list_amis()

        assert result['amis'][0]['tags'].get('stable', 'false') == 'false'
