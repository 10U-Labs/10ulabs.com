import json


def handler(_event, _context):
    status_data = {
        'status': 'healthy',
        'service': '10U Labs API',
        'version': '1.0.0'
    }
    response_headers = {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
    return {'statusCode': 200, 'headers': response_headers, 'body': json.dumps(status_data)}
