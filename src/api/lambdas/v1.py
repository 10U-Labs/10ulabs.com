import base64
import json
import logging
import os
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients = {}
_github_token_cache = {'value': None}
_api_key_cache = {'value': None}
_test_mode = {'enabled': False}


def is_test_mode() -> bool:
    return _test_mode['enabled']


def set_test_mode(enabled: bool):
    _test_mode['enabled'] = enabled


def get_header_case_insensitive(headers: dict, header_name: str) -> str:
    if not headers:
        return ''
    for key, value in headers.items():
        if key.lower() == header_name.lower():
            return value or ''
    return ''


def get_ec2_client():
    if 'ec2' not in _clients:
        _clients['ec2'] = boto3.client('ec2')
    return _clients['ec2']


def get_ecs_client():
    if 'ecs' not in _clients:
        _clients['ecs'] = boto3.client('ecs')
    return _clients['ecs']


def get_ecr_client():
    if 'ecr' not in _clients:
        _clients['ecr'] = boto3.client('ecr')
    return _clients['ecr']


def get_ssm_client():
    if 'ssm' not in _clients:
        _clients['ssm'] = boto3.client('ssm')
    return _clients['ssm']


def get_api_key() -> str:
    api_key = _api_key_cache['value']
    if api_key:
        return api_key
    parameter_name = os.environ['API_KEY_PARAMETER_NAME']
    ssm = get_ssm_client()
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    api_key = response['Parameter']['Value']
    _api_key_cache['value'] = api_key
    return api_key


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body)
    }


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    status_code = 200 if data.get('success', True) else 500
    return json_response(status_code, data)


def error_response(status_code: int, error: str, details: str | None = None) -> Dict[str, Any]:
    body = {'success': False, 'error': error}
    if details:
        body['details'] = details
    return json_response(status_code, body)


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get('body', {})
    result = json.loads(body) if isinstance(body, str) else body
    return result


def is_capacity_error(result: Dict[str, Any]) -> bool:
    error = result.get('error', [])
    if isinstance(error, str):
        return 'capacity' in error.lower() or 'availability zone' in error.lower()
    if isinstance(error, list):
        return any('Capacity' in str(e.get('reason', '')) for e in error if isinstance(e, dict))
    return False


def trigger_github_workflow(workflow_file: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    github_repo = os.environ['GITHUB_REPO']
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


def delete_ecr_image(image_digest: str) -> Dict[str, Any]:
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


def get_github_token() -> str:
    if _github_token_cache['value']:
        return _github_token_cache['value']

    parameter_name = os.environ['GITHUB_TOKEN_SECRET_NAME']
    try:
        response = get_ssm_client().get_parameter(Name=parameter_name, WithDecryption=True)
        token = response['Parameter']['Value']
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
    api_endpoint = os.environ['IMAGE_API_ENDPOINT']
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

    github_token = get_github_token()
    if not github_token:
        logger.error("GITHUB_TOKEN not set - cannot register runner")
        return {'success': False, 'job_id': job_id, 'error': 'GITHUB_TOKEN not configured'}

    registration_token = get_runner_registration_token(github_token, github_repo)
    if not registration_token:
        logger.error("Failed to get runner registration token")
        return {'success': False, 'job_id': job_id, 'error': 'Failed to get runner registration token'}

    runner_name = f'fargate-runner-{job_id}'
    runner_labels = ','.join(job_labels)
    last_error = None

    for subnet in subnets:
        try:
            response = get_ecs_client().run_task(
                cluster=cluster,
                taskDefinition=task_definition,
                enableECSManagedTags=True,
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': [subnet],
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
                overrides={
                    'containerOverrides': [
                        {
                            'name': os.environ['CONTAINER_NAME'],
                            'command': [
                                '--repo', github_repo,
                                '--name', runner_name,
                                '--labels', runner_labels,
                                '--token', registration_token
                            ]
                        }
                    ]
                },
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
                return {
                    'success': True,
                    'task_arn': task_arn,
                    'job_id': job_id,
                    'runner_type': 'fargate-spot'
                }

            failures = response.get('failures', [])
            is_capacity_error = any('Capacity' in str(f.get('reason', '')) for f in failures)
            if is_capacity_error:
                logger.warning("No Fargate Spot capacity in subnet %s, trying next AZ...", subnet)
                last_error = failures
                continue

            logger.error("❌ Failed to launch Fargate runner for job %s: %s", job_id, failures)
            return {'success': False, 'job_id': job_id, 'error': failures}

        except ClientError as e:
            logger.error("❌ Error launching Fargate runner for job %s: %s", job_id, e)
            return {'success': False, 'job_id': job_id, 'error': str(e)}

    logger.error("❌ Failed to launch Fargate runner for job %s: no capacity in any AZ", job_id)
    error_msg = last_error if last_error else 'No capacity in any availability zone'
    return {'success': False, 'job_id': job_id, 'error': error_msg}


def get_runner_registration_token(github_token: str, github_repo: str) -> str:
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    req = urllib.request.Request(
        f'https://api.github.com/repos/{github_repo}/actions/runners/registration-token',
        method='POST',
        headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            return data.get('token', '')
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
        logger.error("Failed to get runner registration token: %s", e)
        return ''


def create_ec2_user_data(registration_token: str, job_labels: List[str], github_repo: str) -> str:
    aws_region = os.environ['AWS_REGION']
    runner_labels = ','.join(job_labels)
    return f"""#!/bin/bash
set -e

cd /home/github-runner/actions-runner

sudo -u github-runner ./config.sh \
    --url "https://github.com/{github_repo}" \
    --token "{registration_token}" \
    --name "ec2-spot-$(hostname)" \
    --labels "{runner_labels}" \
    --ephemeral \
    --unattended

sudo -u github-runner ./run.sh

INSTANCE_ID=$(ec2-metadata --instance-id | cut -d' ' -f2)
aws ec2 terminate-instances \
    --instance-ids "$INSTANCE_ID" \
    --region {aws_region} \
    || shutdown -h now
"""


def get_latest_ami() -> str:
    ami_purpose_tag = os.environ['EC2_AMI_PURPOSE_TAG']
    ami_purpose_value = os.environ['EC2_AMI_PURPOSE_VALUE']
    ami_stable_tag = os.environ['EC2_AMI_STABLE_TAG']
    try:
        response = get_ec2_client().describe_images(
            Owners=['self'],
            Filters=[
                {'Name': f'tag:{ami_purpose_tag}', 'Values': [ami_purpose_value]},
                {'Name': f'tag:{ami_stable_tag}', 'Values': ['true']},
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
    api_domain = os.environ['API_DOMAIN']
    ami_creation_url = f"https://{api_domain}/v1/image-for-ec2-runners"

    try:
        api_key = get_api_key()
        req = urllib.request.Request(
            ami_creation_url,
            data=json.dumps({}).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'x-api-key': api_key},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            logger.info("AMI creation triggered successfully: %s", result)
            return {'success': True, 'result': result}
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError, ClientError) as e:
        logger.error("Failed to trigger AMI creation: %s", e)
        return {'success': False, 'error': str(e)}


def get_ec2_config() -> Dict[str, Any]:
    return {
        'subnet_ids': os.environ['SUBNETS'].split(','),
        'security_group_id': os.environ['SECURITY_GROUPS'],
        'instance_types': os.environ['EC2_INSTANCE_TYPES'].split(','),
        'iam_instance_profile': os.environ['EC2_IAM_INSTANCE_PROFILE'],
        'max_price': os.environ['EC2_MAX_PRICE']
    }


def wait_for_instance_describable(instance_id: str, max_attempts: int = 3) -> Dict[str, Any]:
    ec2 = get_ec2_client()
    attempt = 0
    while attempt < max_attempts:
        try:
            response = ec2.describe_instances(InstanceIds=[instance_id])
            if response['Reservations'] and response['Reservations'][0]['Instances']:
                return response['Reservations'][0]['Instances'][0]
        except ClientError as e:
            if e.response['Error']['Code'] != 'InvalidInstanceID.NotFound':
                raise
        wait_time = 2 ** (attempt + 3)
        time.sleep(wait_time)
        attempt = attempt + 1
    raise ClientError(
        {'Error': {'Code': 'InvalidInstanceID.NotFound', 'Message': f'Instance {instance_id} not found after {max_attempts} attempts'}},
        'DescribeInstances'
    )


def create_fleet_launch_template(template_config: Dict[str, Any]) -> str:
    ec2 = get_ec2_client()
    template_name = f"github-runner-fleet-{template_config['job_id']}"
    try:
        response = ec2.create_launch_template(
            LaunchTemplateName=template_name,
            LaunchTemplateData={
                'ImageId': template_config['ami_id'],
                'SecurityGroupIds': [template_config['security_group_id']],
                'IamInstanceProfile': {'Name': template_config['iam_instance_profile']},
                'UserData': template_config['user_data_base64'],
                'MetadataOptions': {
                    'HttpTokens': 'required',
                    'HttpEndpoint': 'enabled'
                },
                'TagSpecifications': [{
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': f"github-runner-ec2-{template_config['job_id']}"},
                        {'Key': 'Type', 'Value': 'ephemeral-runner'},
                        {'Key': 'ManagedBy', 'Value': 'api-ec2-spot-runner'},
                        {'Key': 'GitHubJobId', 'Value': str(template_config['job_id'])},
                        {'Key': 'JobLabels', 'Value': ','.join(template_config['job_labels'])},
                        {'Key': 'GitHubRepo', 'Value': template_config['github_repo']}
                    ]
                }]
            }
        )
        return response['LaunchTemplate']['LaunchTemplateId']
    except ClientError as e:
        logger.error("Failed to create launch template: %s", e)
        raise


def delete_launch_template(template_id: str):
    try:
        get_ec2_client().delete_launch_template(LaunchTemplateId=template_id)
    except ClientError as e:
        logger.warning("Failed to delete launch template %s: %s", template_id, e)


def launch_ec2_spot_runner(job_id: int, job_labels: List[str], github_repo: str) -> Dict[str, Any]:
    ami_id = get_latest_ami()
    github_token = get_github_token()
    config = get_ec2_config()

    if not ami_id:
        logger.warning("No AMI available - triggering AMI creation")
        ami_trigger = trigger_ami_creation()
        error_msg = 'No AMI available - AMI creation has been triggered. Please retry in a few minutes.'
        if not ami_trigger['success']:
            error_msg = f"No AMI available and failed to trigger creation: {ami_trigger.get('error')}"
        return {
            'success': False,
            'job_id': job_id,
            'error': error_msg,
            'ami_creation_triggered': ami_trigger['success']
        }

    if not github_token:
        logger.error("GITHUB_TOKEN not set - cannot register runner")
        return {'success': False, 'job_id': job_id, 'error': 'GITHUB_TOKEN not configured'}

    registration_token = get_runner_registration_token(github_token, github_repo)
    if not registration_token:
        logger.error("Failed to get runner registration token")
        return {'success': False, 'job_id': job_id, 'error': 'Failed to get runner registration token'}

    user_data = create_ec2_user_data(registration_token, job_labels, github_repo)
    user_data_base64 = base64.b64encode(user_data.encode('utf-8')).decode('utf-8')

    template_config = {
        'ami_id': ami_id,
        'security_group_id': config['security_group_id'],
        'iam_instance_profile': config['iam_instance_profile'],
        'user_data_base64': user_data_base64,
        'job_id': job_id,
        'job_labels': job_labels,
        'github_repo': github_repo
    }

    launch_template_id = None
    try:
        launch_template_id = create_fleet_launch_template(template_config)

        fleet_response = get_ec2_client().create_fleet(
            Type='instant',
            TargetCapacitySpecification={
                'TotalTargetCapacity': 1,
                'DefaultTargetCapacityType': 'spot'
            },
            SpotOptions={
                'AllocationStrategy': 'capacity-optimized',
                'InstanceInterruptionBehavior': 'terminate'
            },
            LaunchTemplateConfigs=[{
                'LaunchTemplateSpecification': {
                    'LaunchTemplateId': launch_template_id,
                    'Version': '$Latest'
                },
                'Overrides': [
                    {'InstanceType': instance_type, 'SubnetId': subnet_id, 'MaxPrice': config['max_price']}
                    for subnet_id in config['subnet_ids']
                    for instance_type in config['instance_types']
                ]
            }]
        )

        if fleet_response.get('Instances'):
            instance_ids = fleet_response['Instances'][0].get('InstanceIds', [])
            if instance_ids:
                instance_id = instance_ids[0]
                instance = wait_for_instance_describable(instance_id)
                logger.info(
                    "Launched EC2 spot runner for job %s: %s (%s in %s)",
                    job_id,
                    instance_id,
                    instance['InstanceType'],
                    instance['Placement']['AvailabilityZone']
                )
                return {
                    'success': True,
                    'instance_id': instance_id,
                    'instance_type': instance['InstanceType'],
                    'availability_zone': instance['Placement']['AvailabilityZone'],
                    'job_id': job_id,
                    'runner_type': 'ec2-spot'
                }

        errors = fleet_response.get('Errors', [])
        error_msg = '; '.join([e.get('ErrorMessage', str(e)) for e in errors]) if errors else 'No instances launched'
        logger.error("❌ Failed to launch EC2 runner for job %s: %s", job_id, error_msg)
        return {'success': False, 'job_id': job_id, 'error': error_msg}

    except ClientError as e:
        logger.error("Error launching EC2 runner for job %s: %s", job_id, e)
        return {'success': False, 'job_id': job_id, 'error': str(e)}
    finally:
        if launch_template_id:
            delete_launch_template(launch_template_id)


def launch_packer_builder(_config: Dict[str, Any]) -> Dict[str, Any]:
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

    result = trigger_github_workflow('image_for_ec2_runners_post.yml', payload)
    return result


def list_amis() -> Dict[str, Any]:
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
        elif is_test_mode():
            response = success_response(TEST_MODE_MOCK_PATHS['/v1/docker-runner'])
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
                capacity_error = not result.get('success') and is_capacity_error(result)
                status_code = 503 if capacity_error else (200 if result.get('success') else 500)
                response = json_response(status_code, response_body)
    except (ValueError, KeyError) as e:
        logger.error("Error handling POST request: %s", e, exc_info=True)
        response = error_response(500, 'Internal server error', str(e))
    return response


def get_docker_runner_status() -> Dict[str, Any]:
    cluster = os.environ['ECS_CLUSTER']
    try:
        ecs = get_ecs_client()
        response = ecs.list_tasks(
            cluster=cluster,
            desiredStatus='RUNNING'
        )

        task_arns = response.get('taskArns', [])

        if not task_arns:
            result = {
                'success': True,
                'running_tasks': 0,
                'tasks': [],
                'cluster': cluster
            }
        else:
            task_details = ecs.describe_tasks(
                cluster=cluster,
                tasks=task_arns
            )

            tasks = []
            for task in task_details.get('tasks', []):
                task_tags = {tag['key']: tag['value'] for tag in task.get('tags', [])}
                tasks.append({
                    'task_arn': task['taskArn'],
                    'task_id': task['taskArn'].split('/')[-1],
                    'status': task['lastStatus'],
                    'desired_status': task['desiredStatus'],
                    'started_at': task.get('startedAt').isoformat() if task.get('startedAt') else None,
                    'cpu': task.get('cpu'),
                    'memory': task.get('memory'),
                    'job_id': task_tags.get('GitHubJobId'),
                    'job_labels': task_tags.get('JobLabels'),
                    'github_repo': task_tags.get('GitHubRepo')
                })

            result = {
                'success': True,
                'running_tasks': len(tasks),
                'tasks': tasks,
                'cluster': cluster
            }

        logger.info("Docker runner status: %d running tasks", len(task_arns))
        return result
    except ClientError as e:
        logger.error("Error getting docker runner status: %s", e)
        return {
            'success': False,
            'error': str(e)
        }


def get_ec2_runner_status() -> Dict[str, Any]:
    try:
        ec2 = get_ec2_client()
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:Type', 'Values': ['ephemeral-runner']},
                {'Name': 'tag:ManagedBy', 'Values': ['api-ec2-spot-runner']},
                {'Name': 'instance-state-name', 'Values': ['pending', 'running']}
            ]
        )

        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                instances.append({
                    'instance_id': instance['InstanceId'],
                    'instance_type': instance['InstanceType'],
                    'state': instance['State']['Name'],
                    'availability_zone': instance['Placement']['AvailabilityZone'],
                    'launch_time': instance['LaunchTime'].isoformat(),
                    'public_ip': instance.get('PublicIpAddress'),
                    'job_id': instance_tags.get('GitHubJobId'),
                    'job_labels': instance_tags.get('JobLabels'),
                    'github_repo': instance_tags.get('GitHubRepo')
                })

        result = {
            'success': True,
            'running_instances': len(instances),
            'instances': instances
        }
        logger.info("EC2 runner status: %d running instances", len(instances))
        return result
    except ClientError as e:
        logger.error("Error getting EC2 runner status: %s", e)
        return {
            'success': False,
            'error': str(e)
        }


def handle_docker_runner_get(event: Dict[str, Any]) -> Dict[str, Any]:
    result = get_docker_runner_status()
    response = success_response(result)
    return response


def handle_ec2_runner_get(event: Dict[str, Any]) -> Dict[str, Any]:
    result = get_ec2_runner_status()
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
        elif is_test_mode():
            response = success_response(TEST_MODE_MOCK_PATHS['/v1/ec2-runner'])
        else:
            result = launch_ec2_spot_runner(job_id, job_labels, github_repo)
            response_body = result.copy()
            capacity_error = not result.get('success') and is_capacity_error(result)
            status_code = 503 if capacity_error else (200 if result.get('success') else 500)
            response = json_response(status_code, response_body)
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
    ('/v1/ec2-runner', 'GET'): handle_ec2_runner_get,
    ('/v1/image-for-docker-runners', 'POST'): lambda e: handle_post_request(e, trigger_docker_image_build),
    ('/v1/image-for-docker-runners', 'GET'): handle_docker_image_get,
    ('/v1/image-for-docker-runners/latest', 'GET'): handle_docker_image_get,
    ('/v1/image-for-ec2-runners', 'POST'): lambda e: handle_post_request(e, launch_packer_builder),
    ('/v1/image-for-ec2-runners', 'GET'): handle_ec2_image_get,
    ('/v1/image-for-ec2-runners/latest', 'GET'): handle_ec2_image_get
}


TEST_MODE_MOCK_PATHS = {
    '/v1/ec2-runner': {'success': True, 'instance_id': 'i-test-mode-mock', 'test_mode': True},
    '/v1/docker-runner': {'success': True, 'task_arn': 'arn:aws:ecs:test-mode-mock', 'test_mode': True},
    '/v1/image-for-ec2-runners': {'success': True, 'message': 'Test mode - no AMI created', 'test_mode': True},
    '/v1/image-for-docker-runners': {'success': True, 'message': 'Test mode - no image built', 'test_mode': True}
}


def lambda_handler(event, _context):
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
        if path.startswith('/v1/image-for-docker-runners/') and method == 'DELETE':
            handler = handle_docker_image_delete
        elif path.startswith('/v1/image-for-ec2-runners/') and method == 'DELETE':
            handler = handle_ec2_image_delete

    if handler:
        response = handler(event)
    else:
        response = error_response(404, 'Not found')

    return response
