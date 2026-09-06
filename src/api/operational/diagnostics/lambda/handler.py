from typing import Any, Dict

from lambda_http import dispatch, json_response, parse_body


def handle_echo_post(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        body = parse_body(event)
        request_id = event.get('requestContext', {}).get('requestId', 'N/A')
        response = json_response(200, {'echo': body, 'received_at': request_id})
    except (ValueError, KeyError):
        response = json_response(400, {'success': False, 'error': 'Invalid JSON'})
    return response


def _is_echo(path: str, method: str) -> bool:
    return path == '/diagnostics/echo' and method == 'POST'


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    return dispatch(event, (
        (_is_echo, handle_echo_post),
    ))
