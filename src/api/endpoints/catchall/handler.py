import json


def handler(event, context):
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
