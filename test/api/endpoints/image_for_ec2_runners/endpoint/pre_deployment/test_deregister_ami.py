from botocore.exceptions import ClientError


class TestDeregisterAmi:

    def test_successful_deregistration_returns_success(self, handler_module, mock_ec2):
        mock_ec2.deregister_image.return_value = {}

        result = handler_module.deregister_ami('ami-123')

        assert result['success'] is True

    def test_successful_deregistration_calls_deregister_image(self, handler_module, mock_ec2):
        mock_ec2.deregister_image.return_value = {}

        handler_module.deregister_ami('ami-123')

        mock_ec2.deregister_image.assert_called_once_with(ImageId='ami-123')

    def test_handles_invalid_ami_id(self, handler_module, mock_ec2):
        mock_ec2.deregister_image.side_effect = ClientError(
            {'Error': {'Code': 'InvalidAMIID.Malformed'}}, 'deregister_image'
        )

        result = handler_module.deregister_ami('invalid-ami')

        assert result['success'] is False

    def test_handles_ami_not_found(self, handler_module, mock_ec2):
        mock_ec2.deregister_image.side_effect = ClientError(
            {'Error': {'Code': 'InvalidAMIID.NotFound'}}, 'deregister_image'
        )

        result = handler_module.deregister_ami('ami-notfound')

        assert result['success'] is False
