"""Lambda handler for unmatched API Gateway routes."""
import json


def handler(event, _context):
    """Return a 404 response for requests that don't match any defined route."""
    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': 'Not Found',
            'message': 'The requested endpoint does not exist',
            'path': event.get('path', 'unknown')
        })
    }
