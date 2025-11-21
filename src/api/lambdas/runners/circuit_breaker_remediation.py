import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def check_circuit_breaker_health(function_name: str) -> dict:
    lambda_client = boto3.client('lambda')

    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'httpMethod': 'GET',
                'path': '/v1/runners/health',
                'headers': {}
            })
        )

        payload = json.loads(response['Payload'].read())
        if payload.get('statusCode') == 200:
            body = json.loads(payload.get('body', '{}'))
            return body
        return {'circuit_breaker_state': 'unknown', 'error': 'Health check failed'}

    except ClientError as e:
        logger.error("Failed to check circuit breaker health: %s", e)
        return {'circuit_breaker_state': 'unknown', 'error': str(e)}


def handler(event, context):
    del event, context
    webhook_function_name = os.environ.get('WEBHOOK_FUNCTION_NAME')

    if not webhook_function_name:
        logger.error("WEBHOOK_FUNCTION_NAME not set")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Configuration error'})}

    health_status = check_circuit_breaker_health(webhook_function_name)
    circuit_state = health_status.get('circuit_breaker_state')

    logger.info("Circuit breaker state: %s", circuit_state)

    result = {
        'circuit_breaker_state': circuit_state,
        'action': 'none'
    }

    if circuit_state == 'open':
        logger.warning("Circuit breaker is open - will auto-recover via timeout mechanism")
        result['action'] = 'monitored'
        result['note'] = 'Circuit breaker will auto-recover after timeout'

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
