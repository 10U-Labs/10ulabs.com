from unittest.mock import patch, MagicMock

from test.api.pre_deployment.conftest import parse_response_body, assert_no_hardcoded_env_defaults, get_lambda_path
import pytest


def test_no_hardcoded_defaults_in_v1():
    assert_no_hardcoded_env_defaults(get_lambda_path("v1.py"))



@pytest.mark.parametrize("client_name", ["ec2", "ecs", "ecr", "ssm"])
def test_client_caches_on_second_call(v1_handler, client_name):
    with patch('boto3.client') as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        clients_dict = getattr(v1_handler, "_clients")
        clients_dict.clear()
        get_client_method = getattr(v1_handler, f"get_{client_name}_client")
        get_client_method()
        get_client_method()
        assert mock_boto_client.call_count == 1



@pytest.mark.parametrize("client_name", ["ec2", "ecs", "ecr", "ssm"])
def test_client_initialization(v1_handler, client_name):
    with patch('boto3.client') as mock_boto_client:
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        with patch.object(v1_handler, '_clients', {}):
            get_client_method = getattr(v1_handler, f"get_{client_name}_client")
            client = get_client_method()
            assert client is not None
            mock_boto_client.assert_called_once_with(client_name)



def test_json_response_formats_correctly(v1_handler):
    result = v1_handler.json_response(200, {'test': 'data'})
    assert result['statusCode'] == 200



def test_success_response_with_success_true(v1_handler):
    result = v1_handler.success_response({'success': True, 'data': 'test'})
    assert result['statusCode'] == 200



def test_success_response_with_success_false(v1_handler):
    result = v1_handler.success_response({'success': False, 'error': 'test'})
    assert result['statusCode'] == 500



def test_error_response_with_details(v1_handler):
    result = v1_handler.error_response(400, 'Bad Request', 'Invalid input')
    body = parse_response_body(result)
    assert 'details' in body



def test_error_response_without_details(v1_handler):
    result = v1_handler.error_response(400, 'Bad Request')
    body = parse_response_body(result)
    assert body['error'] == 'Bad Request'



def test_parse_body_with_string_body(v1_handler):
    event = {'body': '{"key": "value"}'}
    result = v1_handler.parse_body(event)
    assert result['key'] == 'value'



def test_parse_body_with_dict_body(v1_handler):
    event = {'body': {'key': 'value'}}
    result = v1_handler.parse_body(event)
    assert result['key'] == 'value'
