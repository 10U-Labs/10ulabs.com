class TestListAmis:

    def test_returns_list_with_success(self, handler, mock_ec2):
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

        result = handler.list_amis()

        assert result['success'] is True

    def test_returns_correct_ami_count(self, handler, mock_ec2):
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

        result = handler.list_amis()

        assert len(result['amis']) == 1

    def test_returns_correct_ami_id(self, handler, mock_ec2):
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

        result = handler.list_amis()

        assert result['amis'][0]['ami_id'] == 'ami-123'

    def test_handles_empty_ami_list_returns_success(self, handler, mock_ec2):
        mock_ec2.describe_images.return_value = {'Images': []}

        result = handler.list_amis()

        assert result['success'] is True

    def test_handles_empty_ami_list_returns_empty_array(self, handler, mock_ec2):
        mock_ec2.describe_images.return_value = {'Images': []}

        result = handler.list_amis()

        assert result['amis'] == []

    def test_handles_missing_stable_tag_returns_success(self, handler, mock_ec2):
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

        result = handler.list_amis()

        assert result['success'] is True

    def test_handles_missing_stable_tag_defaults_to_false(self, handler, mock_ec2):
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

        result = handler.list_amis()

        assert result['amis'][0]['tags'].get('stable', 'false') == 'false'
