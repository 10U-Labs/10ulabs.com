from typing import Any, Dict

from lambda_http import dispatch, json_response


def handle_health(_event: Dict[str, Any]) -> Dict[str, Any]:
    status_data = {
        'status': 'healthy',
        'service': '10U Labs API',
        'version': '1.0.0'
    }
    return json_response(200, status_data)


def _is_health(path: str, method: str) -> bool:
    return path == '/health' and method == 'GET'


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    return dispatch(event, (
        (_is_health, handle_health),
    ))
