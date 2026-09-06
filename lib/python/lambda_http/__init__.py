import base64
import json
from typing import Any, Callable, Dict, Sequence, Tuple


CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-test-mode'
}


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json', **CORS_HEADERS},
        'body': json.dumps(body)
    }


def error_response(status_code: int, message: str, details: str = '') -> Dict[str, Any]:
    body: Dict[str, Any] = {'success': False, 'error': message}
    if details:
        body['details'] = details
    return json_response(status_code, body)


def options_response() -> Dict[str, Any]:
    return {
        'statusCode': 200,
        'headers': dict(CORS_HEADERS),
        'body': ''
    }


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get('body') or {}
    if event.get('isBase64Encoded') and isinstance(body, str):
        body = base64.b64decode(body).decode('utf-8')
    if not isinstance(body, str):
        return body
    return json.loads(body) if body else {}


Route = Tuple[
    Callable[[str, str], bool],
    Callable[[Dict[str, Any]], Dict[str, Any]]
]


def dispatch(event: Dict[str, Any], routes: Sequence[Route]) -> Dict[str, Any]:
    method = event.get('httpMethod', '')
    if method == 'OPTIONS':
        return options_response()
    path = event.get('path', '')
    for matches, route_handler in routes:
        if matches(path, method):
            return route_handler(event)
    return error_response(404, 'Not found')
