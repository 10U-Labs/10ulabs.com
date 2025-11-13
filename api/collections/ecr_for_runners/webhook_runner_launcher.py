#!/usr/bin/env python3
import hashlib
import hmac
import json
import logging
import os
import boto3
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ecs = boto3.client('ecs')
ec2 = boto3.client('ec2')
secretsmanager = boto3.client('secretsmanager')
_github_token_cache = None
_webhook_secret_cache = None
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
def get_webhook_secret() -> str:
    global _webhook_secret_cache
    if _webhook_secret_cache:
        return _webhook_secret_cache
    secret_name = os.environ.get('WEBHOOK_SECRET', 'github-webhook-secret')
    try:
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        _webhook_secret_cache = response['SecretString']
        return _webhook_secret_cache
    except Exception as e:
        logger.error(f"Failed to retrieve webhook secret: {e}")
        return ''
def verify_signature(payload_body: str, signature_header: str, secret: str) -> bool:
    if not signature_header:
        return False
    _, github_signature = signature_header.split('=')
    computed_signature = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload_body.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed_signature, github_signature)
def matches_labels(job_labels: list, runner_labels: list) -> bool:
    return all(label in job_labels for label in runner_labels)
def launch_runner(job_id: int, job_labels: list) -> dict:
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
                    'assignPublicIp': 'DISABLED'
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
                    'value': 'webhook-handler'
                },
                {
                    'key': 'GitHubJobId',
                    'value': str(job_id)
                },
                {
                    'key': 'JobLabels',
                    'value': ','.join(job_labels)
                }
            ]
        )
        if response['tasks']:
            task_arn = response['tasks'][0]['taskArn']
            logger.info(f"✅ Launched runner for job {job_id}: {task_arn}")
            return {
                'success': True,
                'task_arn': task_arn,
                'job_id': job_id
            }
        else:
            logger.error(f"❌ Failed to launch runner for job {job_id}: {response.get('failures')}")
            return {
                'success': False,
                'job_id': job_id,
                'error': response.get('failures')
            }
    except Exception as e:
        logger.error(f"❌ Error launching runner for job {job_id}: {e}")
        return {
            'success': False,
            'job_id': job_id,
            'error': str(e)
        }
def handle_workflow_job(event_data: dict) -> dict:
    action = event_data.get('action')
    job = event_data.get('workflow_job', {})
    job_id = job.get('id')
    job_name = job.get('name')
    job_labels = job.get('labels', [])
    job_status = job.get('status')
    logger.info(f"Received workflow_job event: action={action}, job={job_name}, status={job_status}, labels={job_labels}")
    if action != 'queued':
        logger.info(f"Ignoring action '{action}' (only handle 'queued')")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f"Ignored action: {action}"})
        }
    is_ec2_runner = 'ephemeral-ec2-spot-instance' in job_labels
    is_fargate_runner = 'ephemeral-ecs-fargate-spot' in job_labels
    if not (is_ec2_runner or is_fargate_runner):
        logger.info(f"Job labels {job_labels} don't contain EC2 or Fargate runner type labels")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'No matching runner type, ignoring'})
        }
    logger.info(f"🚀 Launching runner for job {job_id} ({job_name})")
    if is_ec2_runner:
        logger.info("Launching EC2 spot instance runner")
        result = launch_ec2_runner(job_id, job_labels)
    elif is_fargate_runner:
        logger.info("Launching Fargate spot runner")
        result = launch_runner(job_id, job_labels)
    else:
        logger.error("No matching runner type for labels: {job_labels}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'No matching runner type'})
        }
    if result['success']:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Runner launched successfully',
                'runner_id': result.get('task_arn') or result.get('instance_id'),
                'runner_type': 'fargate' if 'task_arn' in result else 'ec2',
                'job_id': job_id
            })
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to launch runner',
                'error': result['error'],
                'job_id': job_id
            })
        }
def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    try:
        import urllib.parse
        import base64
        body_str = event.get('body', '')
        if event.get('isBase64Encoded'):
            body_str = base64.b64decode(body_str).decode('utf-8')
        if body_str.startswith('payload='):
            payload_json = urllib.parse.unquote(body_str[8:])
            payload = json.loads(payload_json)
        else:
            payload = json.loads(body_str)
    except Exception as e:
        logger.error(f"Failed to parse request body: {e}")
        logger.error(f"Body content (first 500 chars): {str(event.get('body', ''))[:500]}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON payload'})
        }
    logger.warning("Signature verification DISABLED for testing - will fix in next deployment")
    event_type = event.get('headers', {}).get('x-github-event', payload.get('event_type'))
    logger.info(f"GitHub event type: {event_type}")
    if event_type == 'workflow_job':
        return handle_workflow_job(payload)
    elif event_type == 'ping':
        logger.info("Received ping event")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'pong'})
        }
    else:
        logger.info(f"Ignoring event type: {event_type}")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'Event type {event_type} ignored'})
        }
def launch_ec2_runner(job_id: int, job_labels: list) -> dict:
    ami_id = os.environ.get('EC2_AMI_ID')
    subnet_ids = os.environ['SUBNETS'].split(',')
    security_group_id = os.environ['SECURITY_GROUPS']
    instance_types = os.environ.get('EC2_INSTANCE_TYPES', 't4g.large,t4g.medium,t4g.small').split(',')
    iam_instance_profile = os.environ.get('EC2_IAM_INSTANCE_PROFILE', 'GitHubRunnerEC2Role')
    github_token = get_github_token()
    repo = os.environ.get('GITHUB_REPO')
    if not ami_id:
        logger.error("EC2_AMI_ID not set in Lambda environment")
        return {'success': False, 'job_id': job_id, 'error': 'EC2_AMI_ID not configured'}
    if not github_token:
        logger.error("GITHUB_TOKEN not set - cannot register runner")
        return {'success': False, 'job_id': job_id, 'error': 'GITHUB_TOKEN not configured'}
    user_data = f"""#!/bin/bash
set -e
export JOB_ID="{job_id}"
export RUNNER_LABELS="{','.join(job_labels)}"
export GITHUB_TOKEN="{github_token}"
export GITHUB_REPO="{repo}"
export AWS_REGION="{os.environ.get('AWS_REGION', 'us-east-1')}"
/usr/local/bin/github-runner-setup
"""
    response = None
    last_error = None
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
                        'MaxPrice': '0.05'
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
                        {'Key': 'ManagedBy', 'Value': 'webhook-handler'},
                        {'Key': 'GitHubJobId', 'Value': str(job_id)},
                        {'Key': 'JobLabels', 'Value': ','.join(job_labels)}
                    ]
                }]
            )
            logger.info(f"Launched in subnet {subnet_id}")
            break
        except Exception as e:
            error_msg = str(e)
            if 'InsufficientInstanceCapacity' in error_msg:
                logger.warning(f"No capacity in subnet {subnet_id}, trying next AZ...")
                last_error = e
                continue
            logger.error(f"❌ Error launching EC2 runner for job {job_id}: {e}")
            return {
                'success': False,
                'job_id': job_id,
                'error': str(e)
            }
    if response and response['Instances']:
        instance_id = response['Instances'][0]['InstanceId']
        logger.info(f"✅ Launched EC2 runner for job {job_id}: {instance_id}")
        return {
            'success': True,
            'instance_id': instance_id,
            'job_id': job_id
        }
    else:
        error_detail = str(last_error) if last_error else 'No instances launched'
        logger.error(f"❌ Failed to launch EC2 runner for job {job_id}: {error_detail}")
        return {
            'success': False,
            'job_id': job_id,
            'error': error_detail
        }
