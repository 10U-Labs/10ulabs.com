import json
import os
import re
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError

from test.api.pre_deployment.conftest import parse_response_body, assert_response_status, assert_json_content_type


def test_no_hardcoded_defaults_in_v1():
    lambda_path = Path(__file__).parent.parent.parent / "src" / "api" / "lambdas" / "v1.py"
    with open(lambda_path, 'r', encoding='utf-8') as f:
        content = f.read()

    os_environ_get_pattern_with_default = r"os\.environ\.get\(['\"][^'\"]+['\"],\s*['\"]"

    matches = re.findall(os_environ_get_pattern_with_default, content)
    assert len(matches) == 0



def test_get_ec2_client_caches_on_second_call(v1_handler):
    with patch('boto3.client') as mock_boto_client:
        mock_ec2 = MagicMock()
        mock_boto_client.return_value = mock_ec2
        clients_dict = getattr(v1_handler, "_clients")
        clients_dict.clear()
        v1_handler.get_ec2_client()
        v1_handler.get_ec2_client()
        assert mock_boto_client.call_count == 1



def test_get_ecs_client_caches_on_second_call(v1_handler):
    with patch('boto3.client') as mock_boto_client:
        mock_ecs = MagicMock()
        mock_boto_client.return_value = mock_ecs
        clients_dict = getattr(v1_handler, "_clients")
        clients_dict.clear()
        v1_handler.get_ecs_client()
        v1_handler.get_ecs_client()
        assert mock_boto_client.call_count == 1



def test_get_ecr_client_caches_on_second_call(v1_handler):
    with patch('boto3.client') as mock_boto_client:
        mock_ecr = MagicMock()
        mock_boto_client.return_value = mock_ecr
        clients_dict = getattr(v1_handler, "_clients")
        clients_dict.clear()
        v1_handler.get_ecr_client()
        v1_handler.get_ecr_client()
        assert mock_boto_client.call_count == 1



def test_get_ssm_client_caches_on_second_call(v1_handler):
    with patch('boto3.client') as mock_boto_client:
        mock_ssm = MagicMock()
        mock_boto_client.return_value = mock_ssm
        clients_dict = getattr(v1_handler, "_clients")
        clients_dict.clear()
        v1_handler.get_ssm_client()
        v1_handler.get_ssm_client()
        assert mock_boto_client.call_count == 1



def test_get_ec2_client_initialization(v1_handler):
    with patch('boto3.client') as mock_boto_client:
        mock_ec2 = MagicMock()
        mock_boto_client.return_value = mock_ec2
        with patch.object(v1_handler, '_clients', {}):
            client = v1_handler.get_ec2_client()
            assert client is not None
            mock_boto_client.assert_called_once_with('ec2')



def test_get_ecs_client_initialization(v1_handler):
    with patch('boto3.client') as mock_boto_client:
        mock_ecs = MagicMock()
        mock_boto_client.return_value = mock_ecs
        with patch.object(v1_handler, '_clients', {}):
            client = v1_handler.get_ecs_client()
            assert client is not None
            mock_boto_client.assert_called_once_with('ecs')



def test_get_ecr_client_initialization(v1_handler):
    with patch('boto3.client') as mock_boto_client:
        mock_ecr = MagicMock()
        mock_boto_client.return_value = mock_ecr
        with patch.object(v1_handler, '_clients', {}):
            client = v1_handler.get_ecr_client()
            assert client is not None
            mock_boto_client.assert_called_once_with('ecr')



def test_get_ssm_client_initialization(v1_handler):
    with patch('boto3.client') as mock_boto_client:
        mock_ssm = MagicMock()
        mock_boto_client.return_value = mock_ssm
        with patch.object(v1_handler, '_clients', {}):
            client = v1_handler.get_ssm_client()
            assert client is not None
            mock_boto_client.assert_called_once_with('ssm')



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



