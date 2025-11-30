from unittest.mock import patch
import json


class TestHandleEc2ImageGet:

    def test_calls_get_latest_ami_details(self, v1_handler):
        with patch.object(v1_handler, 'get_latest_ami_details', return_value={'success': True, 'ami_id': 'ami-123'}):
            result = v1_handler.handle_ec2_image_get({'path': '/latest'})

            assert result['statusCode'] == 200

    def test_returns_success_response(self, v1_handler):
        with patch.object(v1_handler, 'get_latest_ami_details', return_value={'success': True, 'ami_id': 'ami-123'}):
            result = v1_handler.handle_ec2_image_get({'path': '/latest'})

            body = json.loads(result['body'])
            assert 'ami_id' in body


class TestHandleEc2ImageDelete:

    def test_extracts_ami_id_from_path(self, v1_handler):
        event = {'pathParameters': {'ami_id': 'ami-123'}}

        with patch.object(v1_handler, 'deregister_ami', return_value={'success': True}) as mock_deregister:
            v1_handler.handle_ec2_image_delete(event)

            mock_deregister.assert_called_once_with('ami-123')

    def test_returns_success_response(self, v1_handler):
        event = {'pathParameters': {'ami_id': 'ami-123'}}

        with patch.object(v1_handler, 'deregister_ami', return_value={'success': True}):
            result = v1_handler.handle_ec2_image_delete(event)

            assert result['statusCode'] == 200

    def test_returns_error_on_failure(self, v1_handler):
        event = {'pathParameters': {'ami_id': 'ami-123'}}

        with patch.object(v1_handler, 'deregister_ami', return_value={'success': False, 'error': 'test error'}):
            result = v1_handler.handle_ec2_image_delete(event)

            assert result['statusCode'] == 500
