from test.api.endpoints.echo.pre_deployment.conftest import parse_response_body, assert_response_status, assert_json_content_type, assert_cors_headers


def test_echo_handler_returns_200_status_code(echo_handler, echo_post_event_factory, lambda_context):
    event = echo_post_event_factory()
    response = echo_handler.handler(event, lambda_context)
    assert_response_status(response, 200)


def test_echo_handler_returns_json_content_type(echo_handler, echo_post_event_factory, lambda_context):
    event = echo_post_event_factory()
    response = echo_handler.handler(event, lambda_context)
    assert_json_content_type(response)


def test_echo_handler_returns_cors_header(echo_handler, echo_post_event_factory, lambda_context):
    event = echo_post_event_factory()
    response = echo_handler.handler(event, lambda_context)
    assert_cors_headers(response)


def test_echo_handler_echoes_input_data(echo_handler, echo_post_event_factory, lambda_context):
    payload = {'message': 'hello', 'number': 42}
    event = echo_post_event_factory(body_data=payload)
    response = echo_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    assert body['echo'] == payload


def test_echo_handler_includes_received_at(echo_handler, echo_post_event_factory, lambda_context):
    event = echo_post_event_factory()
    response = echo_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    assert 'received_at' in body


def test_echo_handler_with_invalid_json_returns_400(echo_handler, echo_post_event_factory, lambda_context):
    event = echo_post_event_factory()
    event['body'] = 'not valid json'
    response = echo_handler.handler(event, lambda_context)
    assert_response_status(response, 400)


def test_echo_handler_body_contains_echo_key(echo_handler, echo_post_event_factory, lambda_context):
    event = echo_post_event_factory()
    response = echo_handler.handler(event, lambda_context)
    body = parse_response_body(response)
    assert 'echo' in body


def test_echo_handler_options_returns_200(echo_handler, lambda_context):
    event = {'path': '/v1/echo', 'httpMethod': 'OPTIONS'}
    response = echo_handler.handler(event, lambda_context)
    assert_response_status(response, 200)


def test_echo_handler_unknown_route_returns_404(echo_handler, lambda_context):
    event = {'path': '/v1/unknown', 'httpMethod': 'POST', 'body': '{}'}
    response = echo_handler.handler(event, lambda_context)
    assert_response_status(response, 404)
