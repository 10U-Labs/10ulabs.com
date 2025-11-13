import json


def handler(event, context):
    path = event.get('path', '')
    http_method = event.get('httpMethod', '')

    if path == '/health' and http_method == 'GET':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'healthy',
                'service': '10U Labs API',
                'version': '1.0.0'
            })
        }

    if path == '/v1/echo' and http_method == 'POST':
        try:
            body = json.loads(event.get('body', '{}'))
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'echo': body,
                    'received_at': context.aws_request_id
                })
            }
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid JSON'
                })
            }

    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': 'Not found'
        })
    }
