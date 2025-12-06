"""Lambda handler for ECS image management API."""
import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Dict
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients: Dict[str, Any] = {}
_test_mode = {'enabled': False}


def is_test_mode() -> bool:
    """Check if test mode is enabled."""
    return _test_mode['enabled']


def set_test_mode(enabled: bool):
    """Enable or disable test mode."""
    _test_mode['enabled'] = enabled


def get_header_case_insensitive(headers: dict, header_name: str) -> str:
    """Get a header value case-insensitively."""
    if not headers:
        return ''
    for key, value in headers.items():
        if key.lower() == header_name.lower():
            return value or ''
    return ''


def get_ecr_client():
    """Get or create cached ECR client."""
    if 'ecr' not in _clients:
        _clients['ecr'] = boto3.client('ecr')
    return _clients['ecr']


def set_client(name, client):
    """Set a client in the cache for testing."""
    _clients[name] = client


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Build a JSON API Gateway response with CORS headers."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-test-mode'
        },
        'body': json.dumps(body)
    }


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Build a success response, using 500 if success is False."""
    status_code = 200 if data.get('success', True) else 500
    return json_response(status_code, data)


def error_response(
    status_code: int, error: str, details: str | None = None
) -> Dict[str, Any]:
    """Build an error response with optional details."""
    body: Dict[str, Any] = {'success': False, 'error': error}
    if details:
        body['details'] = details
    return json_response(status_code, body)


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse request body from string or dict."""
    body = event.get('body', {})
    result = json.loads(body) if isinstance(body, str) else body
    return result


_github_token_cache: Dict[str, str] = {'value': ''}


def get_github_token() -> str:
    """Get GitHub token from SSM Parameter Store."""
    if _github_token_cache['value']:
        return _github_token_cache['value']

    parameter_name = os.environ['GITHUB_TOKEN_SECRET_NAME']
    try:
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        _github_token_cache['value'] = response['Parameter']['Value']
    except ClientError as e:
        logger.error("Failed to retrieve GitHub token: %s", e)
        _github_token_cache['value'] = ''

    return _github_token_cache['value']


def trigger_github_workflow(workflow_file: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Trigger a GitHub Actions workflow dispatch."""
    github_repo = os.environ['GITHUB_REPO']
    github_token = get_github_token()

    if not github_token:
        logger.error("GITHUB_TOKEN not available from SSM")
        result = {'success': False, 'error': 'GITHUB_TOKEN not configured'}
    else:
        base_url = 'https://api.github.com/repos'
        workflow_url = f'{base_url}/{github_repo}/actions/workflows/{workflow_file}/dispatches'

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
                    msg = f'{workflow_file} workflow triggered via GitHub Actions'
                    result = {'success': True, 'message': msg}
                else:
                    logger.warning("Unexpected response status: %s", response.status)
                    err = f'Unexpected response status: {response.status}'
                    result = {'success': False, 'error': err}
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
            logger.error("Failed to trigger GitHub Actions workflow: %s", e)
            result = {'success': False, 'error': str(e)}

    return result


def handle_post_request(event: Dict[str, Any], handler_func) -> Dict[str, Any]:
    """Handle POST request with the provided handler function."""
    try:
        path = event.get('path', '')
        if is_test_mode() and path in TEST_MODE_MOCK_PATHS:
            response = success_response(TEST_MODE_MOCK_PATHS[path])
        else:
            body = parse_body(event)
            result = handler_func(body)
            response = success_response(result)
    except (ValueError, KeyError) as e:
        logger.error("Error handling POST request: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


def list_ecr_images() -> Dict[str, Any]:
    """List all images in the ECR repository."""
    ecr_repo = os.environ['ECR_REPOSITORY']
    try:
        response = get_ecr_client().describe_images(
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


def get_latest_ecr_image() -> Dict[str, Any]:
    """Get the latest stable ECR image."""
    ecr_repo = os.environ['ECR_REPOSITORY']
    try:
        response = get_ecr_client().describe_images(
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


def get_ecr_image_by_digest(image_digest: str) -> Dict[str, Any]:
    """Get ECR image details by digest."""
    ecr_repo = os.environ['ECR_REPOSITORY']
    try:
        response = get_ecr_client().describe_images(
            repositoryName=ecr_repo,
            imageIds=[{'imageDigest': image_digest}]
        )

        images = response.get('imageDetails', [])
        if not images:
            result = {'success': False, 'error': f'Image {image_digest} not found'}
        else:
            image = images[0]
            result = {
                'success': True,
                'digest': image['imageDigest'],
                'tags': image.get('imageTags', []),
                'pushed_at': image['imagePushedAt'].isoformat(),
                'size_bytes': image['imageSizeInBytes'],
                'repository': ecr_repo
            }
            logger.info("Found image: %s", image_digest)
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ImageNotFoundException':
            result = {'success': False, 'error': f'Image {image_digest} not found'}
        else:
            logger.error("Error getting image %s: %s", image_digest, e)
            result = {'success': False, 'error': str(e)}
    return result


def delete_ecr_image(image_digest: str) -> Dict[str, Any]:
    """Delete an ECR image by digest."""
    ecr_repo = os.environ['ECR_REPOSITORY']
    try:
        get_ecr_client().batch_delete_image(
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


def trigger_ecs_image_build(_config: Dict[str, Any]) -> Dict[str, Any]:
    """Trigger the ECS image build workflow."""
    payload = {'ref': 'main', 'inputs': {}}
    result = trigger_github_workflow('image_for_ecs_runners.yml', payload)
    return result


def handle_ecs_image_get(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET requests for ECS images."""
    path = event.get('path', '')
    result = get_latest_ecr_image() if path.endswith('/latest') else list_ecr_images()
    response = success_response(result)
    return response


def handle_ecs_image_get_by_digest(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET request for a specific ECS image by digest."""
    path_params = event.get('pathParameters') or {}
    image_digest = path_params.get('digest')
    if not image_digest:
        response = error_response(400, 'Missing required path parameter: digest')
    else:
        result = get_ecr_image_by_digest(image_digest)
        if not result['success']:
            response = error_response(404, result['error'])
        else:
            response = success_response(result)
    return response


def handle_ecs_image_delete(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle DELETE request for an ECS image."""
    path_params = event.get('pathParameters', {})
    image_digest = path_params.get('digest')
    if not image_digest:
        result = {'success': False, 'error': 'Missing required path parameter: digest'}
        response = error_response(400, result['error'])
    else:
        result = delete_ecr_image(image_digest)
        response = success_response(result)
    return response


ROUTE_MAP = {
    ('/v1/image-for-ecs-runners', 'POST'): lambda e: handle_post_request(
        e, trigger_ecs_image_build
    ),
    ('/v1/image-for-ecs-runners', 'GET'): handle_ecs_image_get,
    ('/v1/image-for-ecs-runners/latest', 'GET'): handle_ecs_image_get,
}


TEST_MODE_MOCK_PATHS = {
    '/v1/image-for-ecs-runners': {
        'success': True,
        'message': 'Test mode - no image built',
        'test_mode': True
    }
}


def lambda_handler(event, _context):
    """Main Lambda handler for ECS image API requests."""
    logger.info("Received API request: %s", json.dumps(event))

    headers = event.get('headers', {})
    test_mode_header = get_header_case_insensitive(headers, 'x-test-mode')
    set_test_mode(test_mode_header == 'true')

    if is_test_mode():
        logger.info("Test mode enabled - will return mock responses for POST requests")

    method = event.get('httpMethod', '')
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-test-mode'
            },
            'body': ''
        }

    path = event.get('path', '')

    handler = ROUTE_MAP.get((path, method))

    if not handler:
        if path.startswith('/v1/image-for-ecs-runners/') and not path.endswith('/latest'):
            if method == 'GET':
                handler = handle_ecs_image_get_by_digest
            elif method == 'DELETE':
                handler = handle_ecs_image_delete

    if handler:
        response = handler(event)
    else:
        response = error_response(404, 'Not found')

    return response
