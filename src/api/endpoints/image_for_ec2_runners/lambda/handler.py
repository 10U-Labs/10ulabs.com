"""Lambda handler for EC2 AMI management endpoints."""
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


def get_ec2_client():
    """Get or create an EC2 client."""
    if 'ec2' not in _clients:
        _clients['ec2'] = boto3.client('ec2')
    return _clients['ec2']


def get_ssm_client():
    """Get or create an SSM client."""
    if 'ssm' not in _clients:
        _clients['ssm'] = boto3.client('ssm')
    return _clients['ssm']


def set_client(name, client):
    """Set a client for testing purposes."""
    _clients[name] = client


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a JSON API Gateway response."""
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
    """Create a success response with appropriate status code."""
    status_code = 200 if data.get('success', True) else 500
    return json_response(status_code, data)


def error_response(
    status_code: int, error: str, details: str | None = None
) -> Dict[str, Any]:
    """Create an error response."""
    body: Dict[str, Any] = {'success': False, 'error': error}
    if details:
        body['details'] = details
    return json_response(status_code, body)


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the request body from an API Gateway event."""
    body = event.get('body', {})
    result = json.loads(body) if isinstance(body, str) else body
    return result


_github_token_cache: Dict[str, str] = {'value': ''}


def get_github_token() -> str:
    """Retrieve GitHub token from SSM Parameter Store."""
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


def trigger_github_workflow(
    workflow_file: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Trigger a GitHub Actions workflow via the API."""
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
    """Handle a POST request with optional test mode mocking."""
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


def launch_packer_builder(_config: Dict[str, Any]) -> Dict[str, Any]:
    """Launch the Packer AMI builder workflow."""
    subnet_ids = os.environ['SUBNETS'].split(',')
    vpc_id = os.environ['VPC_ID']
    region = os.environ['AWS_REGION']

    payload = {
        'ref': 'main',
        'inputs': {
            'vpc_id': vpc_id,
            'subnet_id': subnet_ids[0],
            'region': region
        }
    }

    result = trigger_github_workflow('endpoint_v1_image_for_ec2_runners_post.yml', payload)
    return result


def list_amis() -> Dict[str, Any]:
    """List all AMIs with the configured purpose tag."""
    ami_purpose_tag = os.environ['EC2_AMI_PURPOSE_TAG']
    ami_purpose_value = os.environ['EC2_AMI_PURPOSE_VALUE']
    try:
        response = get_ec2_client().describe_images(
            Owners=['self'],
            Filters=[
                {'Name': f'tag:{ami_purpose_tag}', 'Values': [ami_purpose_value]}
            ]
        )

        amis = []
        for image in response['Images']:
            amis.append({
                'ami_id': image['ImageId'],
                'name': image['Name'],
                'state': image['State'],
                'creation_date': image['CreationDate'],
                'architecture': image['Architecture'],
                'tags': {tag['Key']: tag['Value'] for tag in image.get('Tags', [])}
            })

        amis.sort(key=lambda x: str(x['creation_date']), reverse=True)
        logger.info("Listed %s AMIs", len(amis))
        return {'success': True, 'amis': amis, 'count': len(amis)}
    except ClientError as e:
        logger.error("Error listing AMIs: %s", e)
        return {'success': False, 'error': str(e)}


def get_latest_ami_details() -> Dict[str, Any]:
    """Get details of the latest available AMI."""
    ami_purpose_tag = os.environ['EC2_AMI_PURPOSE_TAG']
    ami_purpose_value = os.environ['EC2_AMI_PURPOSE_VALUE']
    ami_stable_tag = os.environ['EC2_AMI_STABLE_TAG']
    try:
        try:
            param_response = get_ssm_client().get_parameter(Name='/github-runner/ami/latest')
            ami_id = param_response['Parameter']['Value']
            logger.info("Retrieved latest AMI from SSM Parameter Store: %s", ami_id)
        except ClientError as ssm_error:
            if ssm_error.response['Error']['Code'] == 'ParameterNotFound':
                logger.warning("SSM parameter not found, falling back to EC2 query")
                response = get_ec2_client().describe_images(
                    Owners=['self'],
                    Filters=[
                        {'Name': f'tag:{ami_purpose_tag}', 'Values': [ami_purpose_value]},
                        {'Name': f'tag:{ami_stable_tag}', 'Values': ['true']}
                    ]
                )
                if not response['Images']:
                    return {'success': False, 'error': 'No available AMI found'}
                images = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
                ami_id = images[0]['ImageId']
                logger.info("Retrieved latest AMI from EC2 query: %s", ami_id)
            else:
                raise

        image_response = get_ec2_client().describe_images(ImageIds=[ami_id])
        if not image_response['Images']:
            return {'success': False, 'error': f'AMI {ami_id} not found'}

        latest_image = image_response['Images'][0]
        result = {
            'success': True,
            'ami_id': latest_image['ImageId'],
            'name': latest_image['Name'],
            'state': latest_image['State'],
            'creation_date': latest_image['CreationDate'],
            'architecture': latest_image['Architecture'],
            'tags': {tag['Key']: tag['Value'] for tag in latest_image.get('Tags', [])}
        }
        logger.info("Latest AMI details: %s", result['ami_id'])
        return result
    except ClientError as e:
        logger.error("Error getting latest AMI: %s", e)
        return {'success': False, 'error': str(e)}


def deregister_ami(ami_id: str) -> Dict[str, Any]:
    """Deregister an AMI and delete its associated snapshots."""
    try:
        image_response = get_ec2_client().describe_images(ImageIds=[ami_id])
        if not image_response['Images']:
            return {'success': False, 'error': 'AMI not found'}

        snapshot_ids = []
        for mapping in image_response['Images'][0].get('BlockDeviceMappings', []):
            if 'Ebs' in mapping and 'SnapshotId' in mapping['Ebs']:
                snapshot_ids.append(mapping['Ebs']['SnapshotId'])

        get_ec2_client().deregister_image(ImageId=ami_id)
        logger.info("Deregistered AMI: %s", ami_id)

        for snapshot_id in snapshot_ids:
            try:
                get_ec2_client().delete_snapshot(SnapshotId=snapshot_id)
                logger.info("Deleted snapshot: %s", snapshot_id)
            except ClientError as e:
                logger.warning("Failed to delete snapshot %s: %s", snapshot_id, e)

        return {
            'success': True,
            'ami_id': ami_id,
            'deleted_snapshots': snapshot_ids,
            'message': f'AMI {ami_id} deregistered successfully'
        }
    except ClientError as e:
        logger.error("Error deregistering AMI %s: %s", ami_id, e)
        return {'success': False, 'error': str(e)}


def handle_ec2_image_get(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET requests for AMI endpoints."""
    path = event.get('path', '')
    result = get_latest_ami_details() if path.endswith('/latest') else list_amis()
    response = success_response(result)
    return response


def handle_ec2_image_delete(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle DELETE requests to deregister an AMI."""
    path_params = event.get('pathParameters', {})
    ami_id = path_params.get('ami_id')
    if not ami_id:
        error_msg = 'Missing required path parameter: ami_id'
        response = error_response(400, error_msg)
    else:
        result = deregister_ami(ami_id)
        response = success_response(result)
    return response


ROUTE_MAP = {
    ('/v1/image-for-ec2-runners', 'POST'): lambda e: handle_post_request(e, launch_packer_builder),
    ('/v1/image-for-ec2-runners', 'GET'): handle_ec2_image_get,
    ('/v1/image-for-ec2-runners/latest', 'GET'): handle_ec2_image_get,
}


TEST_MODE_MOCK_PATHS = {
    '/v1/image-for-ec2-runners': {
        'success': True,
        'message': 'Test mode - no AMI created',
        'test_mode': True
    }
}


def lambda_handler(event, _context):
    """Main Lambda handler for API Gateway requests."""
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
        if path.startswith('/v1/image-for-ec2-runners/') and method == 'DELETE':
            handler = handle_ec2_image_delete

    if handler:
        response = handler(event)
    else:
        response = error_response(404, 'Not found')

    return response
