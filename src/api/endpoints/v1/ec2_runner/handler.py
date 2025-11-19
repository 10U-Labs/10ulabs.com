#!/usr/bin/env python3
import json
import logging
import os
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')
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


def _create_user_data(job_id: int, job_labels: List[str], github_token: str, github_repo: str) -> str:
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
                {'Name': 'tag:Purpose', 'Values': ['github-actions-runner']},
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


def _get_ec2_config() -> Dict[str, Any]:
    ami_id = os.environ.get('EC2_AMI_ID')
    if not ami_id:
        ami_id = get_latest_ami()

    return {
        'ami_id': ami_id,
        'subnet_ids': os.environ['SUBNETS'].split(','),
        'security_group_id': os.environ['SECURITY_GROUPS'],
        'instance_types': os.environ.get('EC2_INSTANCE_TYPES', 't4g.large,t4g.medium,t4g.small').split(','),
        'iam_instance_profile': os.environ.get('EC2_IAM_INSTANCE_PROFILE', 'GitHubSelfHostedRunnerInstanceProfile'),
        'max_price': os.environ.get('EC2_MAX_PRICE', '0.05')
    }


def launch_ec2_spot_runner(job_id: int, job_labels: List[str], github_repo: str) -> Dict[str, Any]:
    config = _get_ec2_config()
    github_token = get_github_token()

    if not config['ami_id']:
        logger.error("No AMI available - please create one using /v1/image-for-ec2-runners endpoint")
        return {
            'success': False,
            'job_id': job_id,
            'error': 'No AMI available - please create one using /v1/image-for-ec2-runners endpoint'
        }

    if not github_token:
        logger.error("GITHUB_TOKEN not set - cannot register runner")
        return {'success': False, 'job_id': job_id, 'error': 'GITHUB_TOKEN not configured'}

    user_data = _create_user_data(job_id, job_labels, github_token, github_repo)

    response = None
    last_error = None

    for subnet_id in config['subnet_ids']:
        try:
            response = ec2.run_instances(
                ImageId=config['ami_id'],
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
            error_msg = str(e)
            if 'InsufficientInstanceCapacity' in error_msg:
                logger.warning("No capacity in subnet %s, trying next AZ...", subnet_id)
                last_error = e
                continue
            logger.error("Error launching EC2 runner for job %s: %s", job_id, e)
            return {
                'success': False,
                'job_id': job_id,
                'error': str(e)
            }

    if response and response['Instances']:
        instance_id = response['Instances'][0]['InstanceId']
        instance_type = response['Instances'][0]['InstanceType']
        availability_zone = response['Instances'][0]['Placement']['AvailabilityZone']

        logger.info("✅ Launched EC2 spot runner for job %s: %s (%s in %s)",
                   job_id, instance_id, instance_type, availability_zone)

        return {
            'success': True,
            'instance_id': instance_id,
            'instance_type': instance_type,
            'availability_zone': availability_zone,
            'job_id': job_id,
            'runner_type': 'ec2-spot'
        }

    error_detail = str(last_error) if last_error else 'No instances launched'
    logger.error("❌ Failed to launch EC2 runner for job %s: %s", job_id, error_detail)
    return {
        'success': False,
        'job_id': job_id,
        'error': error_detail
    }


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

        result = launch_ec2_spot_runner(job_id, job_labels, github_repo)

        if result['success']:
            status_code = 200
            response_body = {
                'success': True,
                'instance_id': result['instance_id'],
                'instance_type': result['instance_type'],
                'availability_zone': result['availability_zone'],
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
