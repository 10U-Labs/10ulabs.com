import json
from typing import Any, Dict


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }


def handle_health(_event: Dict[str, Any]) -> Dict[str, Any]:
    status_data = {
        'status': 'healthy',
        'service': '10U Labs API',
        'version': '1.0.0'
    }
    return json_response(200, status_data)


ROUTE_MAP = {
    ('/health', 'GET'): handle_health,
}


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    route_key = (path, method)
    route_handler = ROUTE_MAP.get(route_key)
    if route_handler:
        response = route_handler(event)
    else:
        response = json_response(404, {'error': 'Not found'})
    return response
