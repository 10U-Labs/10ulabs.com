class TestListAmis:

    def test_returns_list_with_success(self, v1_handler, mock_ec2):
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-123',
                'Name': 'github-runner-ami',
                'CreationDate': '2024-01-01T00:00:00.000Z',
                'State': 'available',
                'Architecture': 'arm64',
                'Tags': [{'Key': 'stable', 'Value': 'true'}]
            }]
        }

        result = v1_handler.list_amis()

        assert result['success'] is True

    def test_returns_correct_ami_count(self, v1_handler, mock_ec2):
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-123',
                'Name': 'github-runner-ami',
                'CreationDate': '2024-01-01T00:00:00.000Z',
                'State': 'available',
                'Architecture': 'arm64',
                'Tags': [{'Key': 'stable', 'Value': 'true'}]
            }]
        }

        result = v1_handler.list_amis()

        assert len(result['amis']) == 1

    def test_returns_correct_ami_id(self, v1_handler, mock_ec2):
        mock_ec2.describe_images.return_value = {
            'Images': [{
                'ImageId': 'ami-123',
                'Name': 'github-runner-ami',
                'CreationDate': '2024-01-01T00:00:00.000Z',
                'State': 'available',
                'Architecture': 'arm64',
                'Tags': [{'Key': 'stable', 'Value': 'true'}]
            }]
        }

        result = v1_handler.list_amis()

        assert result['amis'][0]['ami_id'] == 'ami-123'

    def test_handles_empty_ami_list_returns_success(self, v1_handler, mock_ec2):
        mock_ec2.describe_images.return_value = {'Images': []}

        result = v1_handler.list_amis()

        assert result['success'] is True

    def test_handles_empty_ami_list_returns_empty_array(self, v1_handler, mock_ec2):
        mock_ec2.describe_images.return_value = {'Images': []}

        result = v1_handler.list_amis()

        assert result['amis'] == []

    def test_handles_missing_stable_tag_returns_success(self, v1_handler, mock_ec2):
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

        result = v1_handler.list_amis()

        assert result['success'] is True

    def test_handles_missing_stable_tag_defaults_to_false(self, v1_handler, mock_ec2):
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

        result = v1_handler.list_amis()

        assert result['amis'][0]['tags'].get('stable', 'false') == 'false'
