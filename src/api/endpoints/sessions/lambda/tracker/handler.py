"""Lambda handler for sessions API - handles session event tracking."""
import base64
import json
import logging
import os
import re
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients: Dict[str, Any] = {}


def clear_clients() -> None:
    """Clear cached boto3 clients."""
    _clients.clear()


def get_dynamodb_client():
    """Get or create cached DynamoDB client."""
    if 'dynamodb' not in _clients:
        _clients['dynamodb'] = boto3.client('dynamodb')
    return _clients['dynamodb']


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Build a JSON API Gateway response with CORS headers."""
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(body)
    }
    return response


def error_response(status_code: int, message: str, details: str = '') -> Dict[str, Any]:
    """Build an error response with optional details."""
    body: Dict[str, Any] = {'success': False, 'error': message}
    if details:
        body['details'] = details
    response = json_response(status_code, body)
    return response


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse request body, handling base64 encoding if present."""
    body = event.get('body', '{}')
    if event.get('isBase64Encoded'):
        body = base64.b64decode(body).decode('utf-8')
    result = json.loads(body) if body else {}
    return result


def validate_analytics_event(event: Dict[str, Any]) -> Optional[str]:
    """Validate an analytics event, returning error message if invalid."""
    error_msg = None
    if 'event_type' not in event:
        error_msg = 'Missing required field: event_type'
    elif 'timestamp' not in event:
        error_msg = 'Missing required field: timestamp'
    elif not isinstance(event['event_type'], str):
        error_msg = 'event_type must be a string'
    elif not isinstance(event['timestamp'], str):
        error_msg = 'timestamp must be a string'
    elif not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', event['timestamp']):
        error_msg = 'timestamp must be in ISO8601 format'
    return error_msg


def validate_analytics_request(body: Dict[str, Any]) -> Optional[str]:
    """Validate an analytics request body, returning error message if invalid."""
    error_msg = None
    if 'device_id' not in body:
        error_msg = 'Missing required field: device_id'
    elif 'events' not in body:
        error_msg = 'Missing required field: events'
    elif not isinstance(body['device_id'], str):
        error_msg = 'device_id must be a string'
    elif not isinstance(body['events'], list):
        error_msg = 'events must be an array'
    elif len(body['events']) == 0:
        error_msg = 'events array cannot be empty'
    elif len(body['events']) > 25:
        error_msg = 'events array cannot exceed 25 items'
    return error_msg


def extract_session_id_from_path(path: str) -> Optional[str]:
    """Extract session_id from path like /v1/sessions/{session_id}/events."""
    match = re.match(r'^/v1/sessions/([^/]+)/events$', path)
    if match:
        return match.group(1)
    return None


def save_analytics_events(
    session_id: str,
    device_id: str,
    events: list,
    session_context: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Save analytics events to DynamoDB."""
    table_name = os.environ['SESSION_EVENTS_TABLE']
    result: Dict[str, Any] = {}
    try:
        write_requests = []
        for event in events:
            item: Dict[str, Any] = {
                'session_id': {'S': session_id},
                'timestamp': {'S': event['timestamp']},
                'device_id': {'S': device_id},
                'event_type': {'S': event['event_type']},
                'event_data': {'S': json.dumps(event)}
            }
            if session_context:
                item['session_context'] = {'S': json.dumps(session_context)}
            write_requests.append({'PutRequest': {'Item': item}})
        get_dynamodb_client().batch_write_item(
            RequestItems={table_name: write_requests}
        )
        logger.info("Saved %d analytics events for session: %s", len(events), session_id)
        result = {'success': True, 'events_saved': len(events)}
    except ClientError as e:
        logger.error("Error saving analytics events: %s", e)
        result = {'success': False, 'error': str(e)}
    return result


def handle_events(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST request to save analytics events."""
    try:
        path = event.get('path', '')
        session_id = extract_session_id_from_path(path)
        if not session_id:
            response = error_response(400, 'Invalid path: missing session_id')
        else:
            body = parse_body(event)
            validation_error = validate_analytics_request(body)
            if validation_error:
                response = error_response(400, validation_error)
            else:
                events_list = body['events']
                event_errors = []
                for i, evt in enumerate(events_list):
                    evt_error = validate_analytics_event(evt)
                    if evt_error:
                        event_errors.append(f'Event {i}: {evt_error}')
                if event_errors:
                    response = error_response(400, 'Invalid events', '; '.join(event_errors))
                else:
                    result = save_analytics_events(
                        session_id,
                        body['device_id'],
                        events_list,
                        body.get('session_context')
                    )
                    if result['success']:
                        response = json_response(200, result)
                    else:
                        response = error_response(500, result['error'])
    except (ValueError, KeyError) as e:
        logger.error("Error handling analytics events: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


def lambda_handler(event, _context):
    """Main Lambda handler for sessions API requests."""
    logger.info("Received API request: %s", json.dumps(event))

    method = event.get('httpMethod', '')
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }

    path = event.get('path', '')

    if path.startswith('/v1/sessions/') and path.endswith('/events') and method == 'POST':
        response = handle_events(event)
    else:
        response = error_response(404, 'Not found')

    return response
