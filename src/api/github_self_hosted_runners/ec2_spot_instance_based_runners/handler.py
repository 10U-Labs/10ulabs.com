#!/usr/bin/env python3
"""
API Handler: Launch EC2 Spot Instance GitHub Self-Hosted Runner

Endpoint: POST /v1/github-self-hosted-runners/ec2-spot-instance-based-runners
"""
import json
import logging
import os
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')
secretsmanager = boto3.client('secretsmanager')

_github_token_cache = None


def get_github_token() -> str:
    """Retrieve GitHub token from Secrets Manager with caching."""
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


def launch_ec2_spot_runner(job_id: int, job_labels: list, github_repo: str) -> dict:
    """
    Launch an EC2 spot instance as a GitHub self-hosted runner.

    Args:
        job_id: GitHub workflow job ID
        job_labels: List of runner labels for the job
        github_repo: GitHub repository in format "owner/repo"

    Returns:
        dict: Result with success status, instance_id, and error if applicable
    """
    ami_id = os.environ.get('EC2_AMI_ID')
    subnet_ids = os.environ['SUBNETS'].split(',')
    security_group_id = os.environ['SECURITY_GROUPS']
    instance_types = os.environ.get('EC2_INSTANCE_TYPES', 't4g.large,t4g.medium,t4g.small').split(',')
    iam_instance_profile = os.environ.get('EC2_IAM_INSTANCE_PROFILE', 'GitHubSelfHostedRunnerInstanceProfile')
    max_price = os.environ.get('EC2_MAX_PRICE', '0.05')

    github_token = get_github_token()

    if not ami_id:
        logger.error("EC2_AMI_ID not set in Lambda environment")
        return {'success': False, 'job_id': job_id, 'error': 'EC2_AMI_ID not configured'}

    if not github_token:
        logger.error("GITHUB_TOKEN not set - cannot register runner")
        return {'success': False, 'job_id': job_id, 'error': 'GITHUB_TOKEN not configured'}

    # User data script to setup GitHub runner on instance startup
    user_data = f"""#!/bin/bash
set -e
export JOB_ID="{job_id}"
export RUNNER_LABELS="{','.join(job_labels)}"
export GITHUB_TOKEN="{github_token}"
export GITHUB_REPO="{github_repo}"
export AWS_REGION="{os.environ.get('AWS_REGION', 'us-east-1')}"
/usr/local/bin/github-runner-setup
"""

    response = None
    last_error = None

    # Try launching in each subnet (AZ) until successful
    for subnet_id in subnet_ids:
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
                        'MaxPrice': max_price
                    }
                },
                InstanceType=instance_types[0],
                SecurityGroupIds=[security_group_id],
                SubnetId=subnet_id,
                IamInstanceProfile={'Name': iam_instance_profile},
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
            logger.info(f"Launched EC2 spot instance in subnet {subnet_id}")
            break
        except Exception as e:
            error_msg = str(e)
            if 'InsufficientInstanceCapacity' in error_msg:
                logger.warning(f"No capacity in subnet {subnet_id}, trying next AZ...")
                last_error = e
                continue
            logger.error(f"Error launching EC2 runner for job {job_id}: {e}")
            return {
                'success': False,
                'job_id': job_id,
                'error': str(e)
            }

    if response and response['Instances']:
        instance_id = response['Instances'][0]['InstanceId']
        instance_type = response['Instances'][0]['InstanceType']
        availability_zone = response['Instances'][0]['Placement']['AvailabilityZone']

        logger.info(f"✅ Launched EC2 spot runner for job {job_id}: {instance_id} ({instance_type} in {availability_zone})")

        return {
            'success': True,
            'instance_id': instance_id,
            'instance_type': instance_type,
            'availability_zone': availability_zone,
            'job_id': job_id,
            'runner_type': 'ec2-spot'
        }
    else:
        error_detail = str(last_error) if last_error else 'No instances launched'
        logger.error(f"❌ Failed to launch EC2 runner for job {job_id}: {error_detail}")
        return {
            'success': False,
            'job_id': job_id,
            'error': error_detail
        }


def lambda_handler(event, context):
    """
    Lambda handler for EC2 spot runner API endpoint.

    Expected input:
    {
        "job_id": 12345,
        "job_labels": ["docker-builder", "arm64"],
        "github_repo": "10U-Foundation/10uf.org"
    }
    """
    logger.info(f"Received API request: {json.dumps(event)}")

    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        # Extract required fields
        job_id = body.get('job_id')
        job_labels = body.get('job_labels', [])
        github_repo = body.get('github_repo')

        # Validate required fields
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

        # Launch EC2 spot runner
        result = launch_ec2_spot_runner(job_id, job_labels, github_repo)

        if result['success']:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': True,
                    'instance_id': result['instance_id'],
                    'instance_type': result['instance_type'],
                    'availability_zone': result['availability_zone'],
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
