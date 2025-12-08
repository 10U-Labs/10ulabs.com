"""Unit tests for crawler trigger Lambda handler."""


def test_lambda_handler_returns_status_code_200(crawler_module):
    """Test that lambda handler returns 200 status code."""
    module, _ = crawler_module
    result = module.lambda_handler({}, None)
    assert result['statusCode'] == 200


def test_lambda_handler_calls_start_crawler(crawler_module):
    """Test that lambda handler calls start_crawler."""
    module, glue_client = crawler_module
    module.lambda_handler({}, None)
    assert glue_client.start_crawler.called


def test_lambda_handler_uses_correct_crawler_name(crawler_module):
    """Test that lambda handler uses correct crawler name."""
    module, glue_client = crawler_module
    module.lambda_handler({}, None)
    glue_client.start_crawler.assert_called_with(Name='test-crawler')


def test_lambda_handler_returns_crawler_name(crawler_module):
    """Test that lambda handler returns crawler name in response."""
    module, _ = crawler_module
    result = module.lambda_handler({}, None)
    assert result['body']['crawler_name'] == 'test-crawler'


def test_lambda_handler_returns_started_status(crawler_module):
    """Test that lambda handler returns started status."""
    module, _ = crawler_module
    result = module.lambda_handler({}, None)
    assert result['body']['status'] == 'started'
