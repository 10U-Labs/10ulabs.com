"""Lambda handler for the echo API endpoint."""
import json
from typing import Any, Dict


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a JSON response with standard headers."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-test-mode'
        },
        'body': json.dumps(body)
    }


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the request body from the Lambda event."""
    body = event.get('body', {})
    result = json.loads(body) if isinstance(body, str) else body
    return result


def handle_echo_post(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST requests to the echo endpoint."""
    try:
        body = parse_body(event)
        request_id = event.get('requestContext', {}).get('requestId', 'N/A')
        response = json_response(200, {'echo': body, 'received_at': request_id})
    except (ValueError, KeyError):
        response = json_response(400, {'success': False, 'error': 'Invalid JSON'})
    return response


ROUTE_MAP = {
    ('/v1/echo', 'POST'): handle_echo_post,
}


def handler(event, _context):
    """Main Lambda handler for routing echo requests."""
    method = event.get('httpMethod', '')
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-test-mode'
            },
            'body': ''
        }

    path = event.get('path', '')
    route_handler = ROUTE_MAP.get((path, method))
    if route_handler:
        response = route_handler(event)
    else:
        response = json_response(404, {'error': 'Not found'})
    return response
