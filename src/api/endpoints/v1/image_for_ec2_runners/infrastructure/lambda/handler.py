import json
import logging
import os
import urllib.request
import urllib.error
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')
ssm = boto3.client('ssm')


def launch_packer_builder(_config: Dict[str, Any]) -> Dict[str, Any]:
    subnet_ids = os.environ['SUBNETS'].split(',')
    vpc_id = os.environ['VPC_ID']
    region = os.environ.get('AWS_REGION', 'us-east-1')
    github_repo = os.environ.get('GITHUB_REPO', '10U-Labs-LLC/10ulabs.com')
    github_token = os.environ.get('GITHUB_TOKEN')

    if not github_token:
        logger.error("GITHUB_TOKEN not set")
        return {
            'success': False,
            'error': 'GITHUB_TOKEN not configured'
        }

    workflow_url = f'https://api.github.com/repos/{github_repo}/actions/workflows/image_for_ec2_runners.yml/dispatches'

    payload = {
        'ref': 'main',
        'inputs': {
            'vpc_id': vpc_id,
            'subnet_id': subnet_ids[0],
            'region': region
        }
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
                    'message': 'AMI build workflow triggered via GitHub Actions'
                }

            logger.warning("Unexpected response status: %s", response.status)
            return {
                'success': False,
                'error': f'Unexpected response status: {response.status}'
            }
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        logger.error("Failed to trigger GitHub Actions workflow: %s", e)
        return {
            'success': False,
            'error': str(e)
        }


def list_amis() -> Dict[str, Any]:
    try:
        response = ec2.describe_images(
            Owners=['self'],
            Filters=[
                {'Name': 'tag:Purpose', 'Values': ['GitHub self-hosted EC2 runner']}
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
        return {
            'success': True,
            'amis': amis,
            'count': len(amis)
        }
    except ClientError as e:
        logger.error("Error listing AMIs: %s", e)
        return {
            'success': False,
            'error': str(e)
        }


def get_latest_ami() -> Dict[str, Any]:
    try:
        try:
            param_response = ssm.get_parameter(
                Name='/github-runner/ami/latest'
            )
            ami_id = param_response['Parameter']['Value']
            logger.info("Retrieved latest AMI from SSM Parameter Store: %s", ami_id)
        except ClientError as ssm_error:
            if ssm_error.response['Error']['Code'] == 'ParameterNotFound':
                logger.warning("SSM parameter not found, falling back to EC2 query")
                response = ec2.describe_images(
                    Owners=['self'],
                    Filters=[
                        {'Name': 'tag:Purpose', 'Values': ['GitHub self-hosted EC2 runner']},
                        {'Name': 'tag:stable', 'Values': ['true']},
                        {'Name': 'state', 'Values': ['available']}
                    ]
                )
                if not response['Images']:
                    return {
                        'success': False,
                        'error': 'No available AMI found'
                    }
                images = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
                ami_id = images[0]['ImageId']
                logger.info("Retrieved latest AMI from EC2 query: %s", ami_id)
            else:
                raise

        image_response = ec2.describe_images(ImageIds=[ami_id])
        if not image_response['Images']:
            return {
                'success': False,
                'error': f'AMI {ami_id} not found'
            }

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
        return {
            'success': False,
            'error': str(e)
        }


def deregister_ami(ami_id: str) -> Dict[str, Any]:
    try:
        image_response = ec2.describe_images(ImageIds=[ami_id])
        if not image_response['Images']:
            return {
                'success': False,
                'error': 'AMI not found'
            }

        snapshot_ids = []
        for mapping in image_response['Images'][0].get('BlockDeviceMappings', []):
            if 'Ebs' in mapping and 'SnapshotId' in mapping['Ebs']:
                snapshot_ids.append(mapping['Ebs']['SnapshotId'])

        ec2.deregister_image(ImageId=ami_id)
        logger.info("Deregistered AMI: %s", ami_id)

        for snapshot_id in snapshot_ids:
            try:
                ec2.delete_snapshot(SnapshotId=snapshot_id)
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

        result = launch_packer_builder(body)

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
        result = get_latest_ami()
    else:
        result = list_amis()

    status_code = 200 if result['success'] else 500
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(result)
    }


def _handle_delete(event: Dict[str, Any]) -> Dict[str, Any]:
    path_params = event.get('pathParameters', {})
    ami_id = path_params.get('ami_id')

    if not ami_id:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'error': 'Missing required path parameter: ami_id'
            })
        }

    result = deregister_ami(ami_id)

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
