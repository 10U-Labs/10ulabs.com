import json
import logging
import os
import urllib.request
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ecs = boto3.client('ecs')
ecr = boto3.client('ecr')
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


def list_images() -> Dict[str, Any]:
    ecr_repo = os.environ.get('ECR_REPOSITORY', 'github-runner')
    try:
        response = ecr.describe_images(
            repositoryName=ecr_repo,
            filter={'tagStatus': 'TAGGED'}
        )

        images = []
        for image in response['imageDetails']:
            image_tags = image.get('imageTags', [])
            if not image_tags:
                continue

            images.append({
                'digest': image['imageDigest'],
                'tags': image_tags,
                'pushed_at': image['imagePushedAt'].isoformat(),
                'size_bytes': image['imageSizeInBytes']
            })

        images.sort(key=lambda x: x['pushed_at'], reverse=True)

        logger.info("Listed %s images", len(images))
        return {
            'success': True,
            'images': images,
            'count': len(images),
            'repository': ecr_repo
        }
    except ClientError as e:
        logger.error("Error listing images: %s", e)
        return {
            'success': False,
            'error': str(e)
        }


def get_latest_image() -> Dict[str, Any]:
    ecr_repo = os.environ.get('ECR_REPOSITORY', 'github-runner')
    try:
        response = ecr.describe_images(
            repositoryName=ecr_repo,
            filter={'tagStatus': 'TAGGED'}
        )

        stable_images = []
        for image in response['imageDetails']:
            image_tags = image.get('imageTags', [])
            if 'stable' in image_tags:
                stable_images.append({
                    'digest': image['imageDigest'],
                    'tags': image_tags,
                    'pushed_at': image['imagePushedAt'],
                    'size_bytes': image['imageSizeInBytes']
                })

        if not stable_images:
            return {
                'success': False,
                'error': 'No stable image found'
            }

        latest_image = sorted(stable_images, key=lambda x: x['pushed_at'], reverse=True)[0]

        result = {
            'success': True,
            'digest': latest_image['digest'],
            'tags': latest_image['tags'],
            'pushed_at': latest_image['pushed_at'].isoformat(),
            'size_bytes': latest_image['size_bytes'],
            'repository': ecr_repo
        }
        logger.info("Latest stable image: %s", result['digest'])
        return result
    except ClientError as e:
        logger.error("Error getting latest image: %s", e)
        return {
            'success': False,
            'error': str(e)
        }


def trigger_image_creation() -> Dict[str, Any]:
    api_endpoint = os.environ.get('IMAGE_API_ENDPOINT', 'https://api.10ulabs.com')
    image_endpoint = f'{api_endpoint}/v1/image-for-docker-runner'

    try:
        req = urllib.request.Request(
            image_endpoint,
            data=json.dumps({}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            logger.info("Image creation triggered: %s", response_data)
            return response_data
    except Exception as e:
        logger.error("Failed to trigger image creation: %s", e)
        return {
            'success': False,
            'error': str(e)
        }


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


def _handle_post(event: Dict[str, Any]) -> Dict[str, Any]:
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

        image_check = get_latest_image()
        if not image_check['success']:
            logger.warning("No stable image found, triggering image creation")
            trigger_result = trigger_image_creation()
            return {
                'statusCode': 202,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': False,
                    'error': 'No stable image available',
                    'message': 'Image build triggered',
                    'trigger_result': trigger_result
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
        logger.error("Error handling POST request: %s", e, exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'details': str(e)
            })
        }


def _handle_get(event: Dict[str, Any]) -> Dict[str, Any]:
    path = event.get('path', '')

    if path.endswith('/latest'):
        result = get_latest_image()
    else:
        result = list_images()

    status_code = 200 if result['success'] else 500
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(result)
    }


def lambda_handler(event, _context):
    logger.info("Received API request: %s", json.dumps(event))

    http_method = event.get('httpMethod', '')

    if http_method == 'POST':
        return _handle_post(event)

    if http_method == 'GET':
        return _handle_get(event)

    return {
        'statusCode': 405,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'error': 'Method not allowed'
        })
    }
