import os
from unittest.mock import patch, MagicMock
from test.rack_designer import load_lambda_module
import pytest


@pytest.fixture(autouse=True)
def set_env_vars():
    os.environ['CRAWLER_NAME'] = 'test-crawler'
    yield
    del os.environ['CRAWLER_NAME']


@pytest.fixture(name="crawler_module")
def crawler_module_fixture():
    with patch('boto3.client') as mock_client:
        mock_glue_client = MagicMock()
        mock_client.return_value = mock_glue_client
        module = load_lambda_module("crawler_trigger.py", "crawler_trigger")
        yield module, mock_glue_client


def test_lambda_handler_returns_status_code_200(crawler_module):
    module, _ = crawler_module
    result = module.lambda_handler({}, None)
    assert result['statusCode'] == 200


def test_lambda_handler_calls_start_crawler(crawler_module):
    module, glue_client = crawler_module
    module.lambda_handler({}, None)
    assert glue_client.start_crawler.called


def test_lambda_handler_uses_correct_crawler_name(crawler_module):
    module, glue_client = crawler_module
    module.lambda_handler({}, None)
    glue_client.start_crawler.assert_called_with(Name='test-crawler')


def test_lambda_handler_returns_crawler_name(crawler_module):
    module, _ = crawler_module
    result = module.lambda_handler({}, None)
    assert result['body']['crawler_name'] == 'test-crawler'


def test_lambda_handler_returns_started_status(crawler_module):
    module, _ = crawler_module
    result = module.lambda_handler({}, None)
    assert result['body']['status'] == 'started'
