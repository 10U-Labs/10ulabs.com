import json
import logging
import os
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ecs = boto3.client('ecs')
secretsmanager = boto3.client('secretsmanager')

_github_token_cache = {'value': None}


def get_github_token() -> str:
    if _github_token_cache['value']:
        return _github_token_cache['value']

    secret_name = os.environ.get('GITHUB_TOKEN_SECRET_NAME', 'github-runner/credentials')
    try:
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(response['SecretString'])
        token = secret_data.get('github_token', '')
        _github_token_cache['value'] = token
        return token
    except (ClientError, ValueError, KeyError) as e:
        logger.error("Failed to retrieve GitHub token: %s", e)
        return ''


def launch_fargate_runner(job_id: int, job_labels: list, github_repo: str) -> Dict[str, Any]:
    cluster = os.environ['ECS_CLUSTER']
    task_definition = os.environ['TASK_DEFINITION']
    subnets = os.environ['SUBNETS'].split(',')
    security_groups = os.environ['SECURITY_GROUPS'].split(',')

    result = {'success': False, 'job_id': job_id, 'error': 'Unknown error'}

    try:
        response = ecs.run_task(
            cluster=cluster,
            taskDefinition=task_definition,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': subnets,
                    'securityGroups': security_groups,
                    'assignPublicIp': 'ENABLED'
                }
            },
            capacityProviderStrategy=[
                {
                    'capacityProvider': 'FARGATE_SPOT',
                    'weight': 100,
                    'base': 0
                }
            ],
            tags=[
                {
                    'key': 'Type',
                    'value': 'ephemeral-runner'
                },
                {
                    'key': 'ManagedBy',
                    'value': 'docker-runner-api'
                },
                {
                    'key': 'GitHubJobId',
                    'value': str(job_id)
                },
                {
                    'key': 'JobLabels',
                    'value': ','.join(job_labels)
                },
                {
                    'key': 'GitHubRepo',
                    'value': github_repo
                }
            ]
        )

        if response['tasks']:
            task_arn = response['tasks'][0]['taskArn']
            logger.info("✅ Launched Fargate runner for job %s: %s", job_id, task_arn)
            result = {
                'success': True,
                'task_arn': task_arn,
                'job_id': job_id,
                'runner_type': 'fargate-spot'
            }
        else:
            failures = response.get('failures')
            logger.error("❌ Failed to launch Fargate runner for job %s: %s", job_id, failures)
            result = {
                'success': False,
                'job_id': job_id,
                'error': failures
            }
    except ClientError as e:
        logger.error("❌ Error launching Fargate runner for job %s: %s", job_id, e)
        result = {
            'success': False,
            'job_id': job_id,
            'error': str(e)
        }

    return result


def lambda_handler(event, _context):
    logger.info("Received API request: %s", json.dumps(event))

    try:
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        job_id = body.get('job_id')
        job_labels = body.get('job_labels', [])
        github_repo = body.get('github_repo')

        if not job_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Missing required field: job_id'
                })
            }

        if not github_repo:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Missing required field: github_repo'
                })
            }

        result = launch_fargate_runner(job_id, job_labels, github_repo)

        if result['success']:
            status_code = 200
            response_body = {
                'success': True,
                'task_arn': result['task_arn'],
                'job_id': result['job_id'],
                'runner_type': result['runner_type']
            }
        else:
            status_code = 500
            response_body = {
                'success': False,
                'error': result['error'],
                'job_id': result['job_id']
            }

        return {
            'statusCode': status_code,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response_body)
        }

    except (ValueError, KeyError) as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }
