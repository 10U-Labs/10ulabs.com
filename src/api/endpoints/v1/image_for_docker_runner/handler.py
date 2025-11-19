import json
import logging
import os
import urllib.request
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ecr = boto3.client('ecr')


def trigger_image_build(_config: Dict[str, Any]) -> Dict[str, Any]:
    github_repo = os.environ.get('GITHUB_REPO', '10U-Labs-LLC/10ulabs.com')
    github_token = os.environ.get('GITHUB_TOKEN')

    if not github_token:
        logger.error("GITHUB_TOKEN not set")
        return {
            'success': False,
            'error': 'GITHUB_TOKEN not configured'
        }

    workflow_url = f'https://api.github.com/repos/{github_repo}/actions/workflows/image_for_docker_runner.yml/dispatches'

    payload = {
        'ref': 'main',
        'inputs': {}
    }

    try:
        req = urllib.request.Request(
            workflow_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Accept': 'application/vnd.github+json',
                'Authorization': f'Bearer {github_token}',
                'X-GitHub-Api-Version': '2022-11-28',
                'Content-Type': 'application/json'
            },
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 204:
                logger.info("GitHub Actions workflow triggered successfully")
                return {
                    'success': True,
                    'message': 'Docker image build workflow triggered via GitHub Actions'
                }

            logger.warning("Unexpected response status: %s", response.status)
            return {
                'success': False,
                'error': f'Unexpected response status: {response.status}'
            }
    except Exception as e:
        logger.error("Failed to trigger GitHub Actions workflow: %s", e)
        return {
            'success': False,
            'error': str(e)
        }


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


def delete_image(image_digest: str) -> Dict[str, Any]:
    ecr_repo = os.environ.get('ECR_REPOSITORY', 'github-runner')
    try:
        ecr.batch_delete_image(
            repositoryName=ecr_repo,
            imageIds=[{'imageDigest': image_digest}]
        )

        logger.info("Deleted image: %s", image_digest)
        return {
            'success': True,
            'digest': image_digest,
            'message': f'Image {image_digest} deleted successfully'
        }
    except ClientError as e:
        logger.error("Error deleting image %s: %s", image_digest, e)
        return {
            'success': False,
            'error': str(e)
        }


def _handle_post(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        result = trigger_image_build(body)

        status_code = 200 if result['success'] else 500
        return {
            'statusCode': status_code,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result)
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


def _handle_delete(event: Dict[str, Any]) -> Dict[str, Any]:
    path_params = event.get('pathParameters', {})
    image_digest = path_params.get('digest')

    if not image_digest:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'error': 'Missing required path parameter: digest'
            })
        }

    result = delete_image(image_digest)

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

    if http_method == 'DELETE':
        return _handle_delete(event)

    return {
        'statusCode': 405,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'error': 'Method not allowed'
        })
    }
