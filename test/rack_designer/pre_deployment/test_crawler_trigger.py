import os
from unittest.mock import patch, MagicMock
import pytest


@pytest.fixture(autouse=True)
def set_env_vars():
    os.environ['CRAWLER_NAME'] = 'test-crawler'
    yield
    del os.environ['CRAWLER_NAME']


@pytest.fixture
def mock_glue():
    with patch('boto3.client') as mock_client:
        mock_glue_client = MagicMock()
        mock_client.return_value = mock_glue_client
        yield mock_glue_client


def test_lambda_handler_returns_status_code_200(mock_glue):
    from src.rack_designer.lambdas.crawler_trigger import lambda_handler
    result = lambda_handler({}, None)
    assert result['statusCode'] == 200


def test_lambda_handler_calls_start_crawler(mock_glue):
    from src.rack_designer.lambdas.crawler_trigger import lambda_handler
    lambda_handler({}, None)
    assert mock_glue.start_crawler.called


def test_lambda_handler_uses_correct_crawler_name(mock_glue):
    from src.rack_designer.lambdas.crawler_trigger import lambda_handler
    lambda_handler({}, None)
    mock_glue.start_crawler.assert_called_with(Name='test-crawler')


def test_lambda_handler_returns_crawler_name(mock_glue):
    from src.rack_designer.lambdas.crawler_trigger import lambda_handler
    result = lambda_handler({}, None)
    assert result['body']['crawler_name'] == 'test-crawler'


def test_lambda_handler_returns_started_status(mock_glue):
    from src.rack_designer.lambdas.crawler_trigger import lambda_handler
    result = lambda_handler({}, None)
    assert result['body']['status'] == 'started'
