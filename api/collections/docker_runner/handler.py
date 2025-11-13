import json
import logging
import os
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ecs = boto3.client('ecs')
secretsmanager = boto3.client('secretsmanager')

_github_token_cache = None


def get_github_token() -> str:
    global _github_token_cache
    if _github_token_cache:
        return _github_token_cache

    secret_name = os.environ.get('GITHUB_TOKEN_SECRET_NAME', 'github-runner/credentials')
    try:
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(response['SecretString'])
        _github_token_cache = secret_data.get('github_token', '')
        return _github_token_cache
    except Exception as e:
        logger.error(f"Failed to retrieve GitHub token: {e}")
        return ''


def launch_fargate_runner(job_id: int, job_labels: list, github_repo: str) -> dict:
    cluster = os.environ['ECS_CLUSTER']
    task_definition = os.environ['TASK_DEFINITION']
    subnets = os.environ['SUBNETS'].split(',')
    security_groups = os.environ['SECURITY_GROUPS'].split(',')

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
            logger.info(f"✅ Launched Fargate runner for job {job_id}: {task_arn}")
            return {
                'success': True,
                'task_arn': task_arn,
                'job_id': job_id,
                'runner_type': 'fargate-spot'
            }
        else:
            logger.error(f"❌ Failed to launch Fargate runner for job {job_id}: {response.get('failures')}")
            return {
                'success': False,
                'job_id': job_id,
                'error': response.get('failures')
            }
    except Exception as e:
        logger.error(f"❌ Error launching Fargate runner for job {job_id}: {e}")
        return {
            'success': False,
            'job_id': job_id,
            'error': str(e)
        }


def lambda_handler(event, context):
    logger.info(f"Received API request: {json.dumps(event)}")

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
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': True,
                    'task_arn': result['task_arn'],
                    'job_id': result['job_id'],
                    'runner_type': result['runner_type']
                })
            }
        else:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': False,
                    'error': result['error'],
                    'job_id': result['job_id']
                })
            }

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }
