from botocore.exceptions import ClientError


class TestGetLatestAmi:

    def test_returns_latest_ami_when_available(self, v1_handler, mock_ec2):
        mock_ec2.describe_images.return_value = {
            'Images': [
                {'ImageId': 'ami-older', 'CreationDate': '2024-01-01T00:00:00.000Z'},
                {'ImageId': 'ami-newer', 'CreationDate': '2024-01-02T00:00:00.000Z'}
            ]
        }

        ami_id = v1_handler.get_latest_ami()

        assert ami_id == 'ami-newer'

    def test_filters_by_purpose_tag(self, v1_handler, mock_ec2):
        mock_ec2.describe_images.return_value = {'Images': []}

        v1_handler.get_latest_ami()

        call_args = mock_ec2.describe_images.call_args
        filters = call_args[1]['Filters']

        assert {'Name': 'tag:Purpose', 'Values': ['GitHub self-hosted EC2 runner']} in filters

    def test_filters_by_stable_tag(self, v1_handler, mock_ec2):
        mock_ec2.describe_images.return_value = {'Images': []}

        v1_handler.get_latest_ami()

        call_args = mock_ec2.describe_images.call_args
        filters = call_args[1]['Filters']

        assert {'Name': 'tag:Stable', 'Values': ['true']} in filters

    def test_returns_empty_string_when_no_amis(self, v1_handler, mock_ec2):
        mock_ec2.describe_images.return_value = {'Images': []}

        ami_id = v1_handler.get_latest_ami()

        assert ami_id == ''

    def test_handles_client_error(self, v1_handler, mock_ec2):
        mock_ec2.describe_images.side_effect = ClientError(
            {'Error': {'Code': 'InvalidParameterValue'}}, 'describe_images'
        )

        ami_id = v1_handler.get_latest_ami()

        assert ami_id == ''
