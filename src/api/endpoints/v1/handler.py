import json
import logging
import os
import urllib.request
import urllib.error
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')
ecs = boto3.client('ecs')
ecr = boto3.client('ecr')
ssm = boto3.client('ssm')
secretsmanager = boto3.client('secretsmanager')

_github_token_cache = {'value': None}


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body)
    }


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    status_code = 200 if data.get('success', True) else 500
    return json_response(status_code, data)


def error_response(status_code: int, error: str, details: str = None) -> Dict[str, Any]:
    body = {'success': False, 'error': error}
    if details:
        body['details'] = details
    return json_response(status_code, body)


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get('body', {})
    result = json.loads(body) if isinstance(body, str) else body
    return result


def trigger_github_workflow(workflow_file: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    github_repo = os.environ.get('GITHUB_REPO', '10U-Labs-LLC/10ulabs.com')
    github_token = os.environ.get('GITHUB_TOKEN')

    if not github_token:
        logger.error("GITHUB_TOKEN not set")
        result = {'success': False, 'error': 'GITHUB_TOKEN not configured'}
    else:
        workflow_url = f'https://api.github.com/repos/{github_repo}/actions/workflows/{workflow_file}/dispatches'

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
                    result = {'success': True, 'message': f'{workflow_file} workflow triggered via GitHub Actions'}
                else:
                    logger.warning("Unexpected response status: %s", response.status)
                    result = {'success': False, 'error': f'Unexpected response status: {response.status}'}
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
            logger.error("Failed to trigger GitHub Actions workflow: %s", e)
            result = {'success': False, 'error': str(e)}

    return result


def handle_post_request(event: Dict[str, Any], handler_func) -> Dict[str, Any]:
    try:
        body = parse_body(event)
        result = handler_func(body)
        response = success_response(result)
    except (ValueError, KeyError) as e:
        logger.error("Error handling POST request: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


def list_ecr_images() -> Dict[str, Any]:
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


def get_latest_ecr_image() -> Dict[str, Any]:
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


def delete_ecr_image(image_digest: str) -> Dict[str, Any]:
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


def trigger_docker_image_build(_config: Dict[str, Any]) -> Dict[str, Any]:
    payload = {'ref': 'main', 'inputs': {}}
    result = trigger_github_workflow('image_for_docker_runner.yml', payload)
    return result


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
            result = response_data
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
        logger.error("Failed to trigger image creation: %s", e)
        result = {'success': False, 'error': str(e)}
    return result


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
                {'key': 'Type', 'value': 'ephemeral-runner'},
                {'key': 'ManagedBy', 'value': 'docker-runner-api'},
                {'key': 'GitHubJobId', 'value': str(job_id)},
                {'key': 'JobLabels', 'value': ','.join(job_labels)},
                {'key': 'GitHubRepo', 'value': github_repo}
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


def _create_ec2_user_data(job_id: int, job_labels: List[str], github_token: str, github_repo: str) -> str:
    return f"""#!/bin/bash
set -e
export JOB_ID="{job_id}"
export RUNNER_LABELS="{','.join(job_labels)}"
export GITHUB_TOKEN="{github_token}"
export GITHUB_REPO="{github_repo}"
export AWS_REGION="{os.environ.get('AWS_REGION', 'us-east-1')}"
/usr/local/bin/github-runner-setup
"""


def get_latest_ami() -> str:
    try:
        response = ec2.describe_images(
            Owners=['self'],
            Filters=[
                {'Name': 'tag:Purpose', 'Values': ['Github self-hosted EC2 runner']},
                {'Name': 'tag:stable', 'Values': ['true']},
                {'Name': 'state', 'Values': ['available']}
            ]
        )

        if not response['Images']:
            logger.warning("No available AMI found")
            return ''

        images = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
        latest_ami_id = images[0]['ImageId']
        logger.info("Found latest AMI: %s", latest_ami_id)
        return latest_ami_id
    except ClientError as e:
        logger.error("Error getting latest AMI: %s", e)
        return ''


def trigger_ami_creation() -> Dict[str, Any]:
    api_domain = os.environ.get('API_DOMAIN', 'api.10ulabs.com')
    ami_creation_url = f"https://{api_domain}/v1/image-for-ec2-runners"

    try:
        req = urllib.request.Request(
            ami_creation_url,
            data=json.dumps({}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            logger.info("AMI creation triggered successfully: %s", result)
            return {'success': True, 'result': result}
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
        logger.error("Failed to trigger AMI creation: %s", e)
        return {'success': False, 'error': str(e)}


def _get_ec2_config() -> Dict[str, Any]:
    return {
        'subnet_ids': os.environ['SUBNETS'].split(','),
        'security_group_id': os.environ['SECURITY_GROUPS'],
        'instance_types': os.environ.get('EC2_INSTANCE_TYPES', 't4g.large,t4g.medium,t4g.small').split(','),
        'iam_instance_profile': os.environ.get('EC2_IAM_INSTANCE_PROFILE', 'GitHubSelfHostedRunnerInstanceProfile'),
        'max_price': os.environ.get('EC2_MAX_PRICE', '0.05')
    }


def launch_ec2_spot_runner(job_id: int, job_labels: List[str], github_repo: str) -> Dict[str, Any]:
    ami_id = get_latest_ami()
    github_token = get_github_token()
    config = _get_ec2_config()

    if not ami_id:
        logger.warning("No AMI available - triggering AMI creation")
        ami_trigger = trigger_ami_creation()
        return {
            'success': False,
            'job_id': job_id,
            'error': 'No AMI available - AMI creation has been triggered. Please retry in a few minutes.' if ami_trigger['success'] else f"No AMI available and failed to trigger creation: {ami_trigger.get('error')}",
            'ami_creation_triggered': ami_trigger['success']
        }

    if not github_token:
        logger.error("GITHUB_TOKEN not set - cannot register runner")
        return {'success': False, 'job_id': job_id, 'error': 'GITHUB_TOKEN not configured'}

    user_data = _create_ec2_user_data(job_id, job_labels, github_token, github_repo)
    response = None
    last_error = None

    for subnet_id in config['subnet_ids']:
        try:
            response = ec2.run_instances(
                ImageId=ami_id,
                MinCount=1,
                MaxCount=1,
                InstanceMarketOptions={
                    'MarketType': 'spot',
                    'SpotOptions': {
                        'SpotInstanceType': 'one-time',
                        'InstanceInterruptionBehavior': 'terminate',
                        'MaxPrice': config['max_price']
                    }
                },
                InstanceType=config['instance_types'][0],
                SecurityGroupIds=[config['security_group_id']],
                SubnetId=subnet_id,
                IamInstanceProfile={'Name': config['iam_instance_profile']},
                UserData=user_data,
                TagSpecifications=[{
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'github-runner-ec2-{job_id}'},
                        {'Key': 'Type', 'Value': 'ephemeral-runner'},
                        {'Key': 'ManagedBy', 'Value': 'api-ec2-spot-runner'},
                        {'Key': 'GitHubJobId', 'Value': str(job_id)},
                        {'Key': 'JobLabels', 'Value': ','.join(job_labels)},
                        {'Key': 'GitHubRepo', 'Value': github_repo}
                    ]
                }]
            )
            logger.info("Launched EC2 spot instance in subnet %s", subnet_id)
            break
        except ClientError as e:
            if 'InsufficientInstanceCapacity' in str(e):
                logger.warning("No capacity in subnet %s, trying next AZ...", subnet_id)
                last_error = e
                continue
            logger.error("Error launching EC2 runner for job %s: %s", job_id, e)
            return {'success': False, 'job_id': job_id, 'error': str(e)}

    if response and response['Instances']:
        instance = response['Instances'][0]
        logger.info("✅ Launched EC2 spot runner for job %s: %s (%s in %s)", job_id, instance['InstanceId'], instance['InstanceType'], instance['Placement']['AvailabilityZone'])
        return {
            'success': True,
            'instance_id': instance['InstanceId'],
            'instance_type': instance['InstanceType'],
            'availability_zone': instance['Placement']['AvailabilityZone'],
            'job_id': job_id,
            'runner_type': 'ec2-spot'
        }

    logger.error("❌ Failed to launch EC2 runner for job %s: %s", job_id, str(last_error) if last_error else 'No instances launched')
    return {'success': False, 'job_id': job_id, 'error': str(last_error) if last_error else 'No instances launched'}


def launch_packer_builder(_config: Dict[str, Any]) -> Dict[str, Any]:
    subnet_ids = os.environ['SUBNETS'].split(',')
    vpc_id = os.environ['VPC_ID']
    region = os.environ.get('AWS_REGION', 'us-east-1')

    payload = {
        'ref': 'main',
        'inputs': {
            'vpc_id': vpc_id,
            'subnet_id': subnet_ids[0],
            'region': region
        }
    }

    result = trigger_github_workflow('image_for_ec2_runners.yml', payload)
    return result


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
        return {'success': True, 'amis': amis, 'count': len(amis)}
    except ClientError as e:
        logger.error("Error listing AMIs: %s", e)
        return {'success': False, 'error': str(e)}


def get_latest_ami_details() -> Dict[str, Any]:
    try:
        try:
            param_response = ssm.get_parameter(Name='/github-runner/ami/latest')
            ami_id = param_response['Parameter']['Value']
            logger.info("Retrieved latest AMI from SSM Parameter Store: %s", ami_id)
        except ClientError as ssm_error:
            if ssm_error.response['Error']['Code'] == 'ParameterNotFound':
                logger.warning("SSM parameter not found, falling back to EC2 query")
                response = ec2.describe_images(
                    Owners=['self'],
                    Filters=[
                        {'Name': 'tag:Purpose', 'Values': ['GitHub self-hosted EC2 runner']},
                        {'Name': 'tag:stable', 'Values': ['true']}
                    ]
                )
                if not response['Images']:
                    return {'success': False, 'error': 'No available AMI found'}
                images = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
                ami_id = images[0]['ImageId']
                logger.info("Retrieved latest AMI from EC2 query: %s", ami_id)
            else:
                raise

        image_response = ec2.describe_images(ImageIds=[ami_id])
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
    try:
        image_response = ec2.describe_images(ImageIds=[ami_id])
        if not image_response['Images']:
            return {'success': False, 'error': 'AMI not found'}

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
        return {'success': False, 'error': str(e)}


def handle_docker_runner_post(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        body = parse_body(event)
        job_id = body.get('job_id')
        job_labels = body.get('job_labels', [])
        github_repo = body.get('github_repo')

        if not job_id:
            response = error_response(400, 'Missing required field: job_id')
        elif not github_repo:
            response = error_response(400, 'Missing required field: github_repo')
        else:
            image_check = get_latest_ecr_image()
            if not image_check['success']:
                logger.warning("No stable image found, triggering image creation")
                trigger_result = trigger_image_creation()
                response = json_response(202, {
                    'success': False,
                    'error': 'No stable image available',
                    'message': 'Image build triggered',
                    'trigger_result': trigger_result
                })
            else:
                result = launch_fargate_runner(job_id, job_labels, github_repo)
                response_body = result.copy()
                response = success_response(response_body)
    except (ValueError, KeyError) as e:
        logger.error("Error handling POST request: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


def handle_docker_runner_get(event: Dict[str, Any]) -> Dict[str, Any]:
    path = event.get('path', '')
    result = get_latest_ecr_image() if path.endswith('/latest') else list_ecr_images()
    response = success_response(result)
    return response


def handle_ec2_runner_post(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        body = parse_body(event)
        job_id = body.get('job_id')
        job_labels = body.get('job_labels', [])
        github_repo = body.get('github_repo')

        if not job_id:
            response = error_response(400, 'Missing required field: job_id')
        elif not github_repo:
            response = error_response(400, 'Missing required field: github_repo')
        else:
            result = launch_ec2_spot_runner(job_id, job_labels, github_repo)
            response_body = result.copy()
            response = success_response(response_body)
    except (ValueError, KeyError) as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


def handle_docker_image_get(event: Dict[str, Any]) -> Dict[str, Any]:
    path = event.get('path', '')
    result = get_latest_ecr_image() if path.endswith('/latest') else list_ecr_images()
    response = success_response(result)
    return response


def handle_docker_image_delete(event: Dict[str, Any]) -> Dict[str, Any]:
    path_params = event.get('pathParameters', {})
    image_digest = path_params.get('digest')
    result = delete_ecr_image(image_digest) if image_digest else {'success': False, 'error': 'Missing required path parameter: digest'}
    response = error_response(400, result['error']) if not image_digest else success_response(result)
    return response


def handle_ec2_image_get(event: Dict[str, Any]) -> Dict[str, Any]:
    path = event.get('path', '')
    result = get_latest_ami_details() if path.endswith('/latest') else list_amis()
    response = success_response(result)
    return response


def handle_ec2_image_delete(event: Dict[str, Any]) -> Dict[str, Any]:
    path_params = event.get('pathParameters', {})
    ami_id = path_params.get('ami_id')
    result = deregister_ami(ami_id) if ami_id else {'success': False, 'error': 'Missing required path parameter: ami_id'}
    response = error_response(400, result['error']) if not ami_id else success_response(result)
    return response


def handle_echo_post(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        body = parse_body(event)
        response = json_response(200, {'echo': body, 'received_at': event.get('requestContext', {}).get('requestId', 'N/A')})
    except (ValueError, KeyError):
        response = error_response(400, 'Invalid JSON')
    return response


ROUTE_MAP = {
    ('/v1/echo', 'POST'): handle_echo_post,
    ('/v1/docker-runner', 'POST'): handle_docker_runner_post,
    ('/v1/docker-runner', 'GET'): handle_docker_runner_get,
    ('/v1/ec2-runner', 'POST'): handle_ec2_runner_post,
    ('/v1/image/docker', 'POST'): lambda e: handle_post_request(e, trigger_docker_image_build),
    ('/v1/image/docker', 'GET'): handle_docker_image_get,
    ('/v1/image/docker', 'DELETE'): handle_docker_image_delete,
    ('/v1/image/ec2', 'POST'): lambda e: handle_post_request(e, launch_packer_builder),
    ('/v1/image/ec2', 'GET'): handle_ec2_image_get,
    ('/v1/image/ec2', 'DELETE'): handle_ec2_image_delete
}


def lambda_handler(event, _context):
    logger.info("Received API request: %s", json.dumps(event))

    path = event.get('path', '')
    method = event.get('httpMethod', '')
    handler = ROUTE_MAP.get((path, method))

    if handler:
        response = handler(event)
    else:
        response = error_response(404, 'Not found')

    return response
