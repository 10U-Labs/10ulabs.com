from test.api.backend.pre_deployment.conftest import parse_response_body, assert_response_status, assert_json_content_type, assert_cors_headers


def test_lambda_handler_catchall_returns_404_for_unknown_path(catchall_handler, catchall_unknown_event, lambda_context):
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert_response_status(response, 404)


def test_lambda_handler_catchall_returns_json_content_type(catchall_handler, catchall_unknown_event, lambda_context):
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert_json_content_type(response)


def test_lambda_handler_catchall_returns_cors_header(catchall_handler, catchall_unknown_event, lambda_context):
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    assert_cors_headers(response)


def test_lambda_handler_catchall_body_contains_error_message(catchall_handler, catchall_unknown_event, lambda_context):
    response = catchall_handler.handler(catchall_unknown_event, lambda_context)
    body = parse_response_body(response)
    assert 'error' in body
