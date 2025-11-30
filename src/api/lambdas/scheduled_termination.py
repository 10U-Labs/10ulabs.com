import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_clients = {}


def get_ecs_client():
    if 'ecs' not in _clients:
        _clients['ecs'] = boto3.client('ecs')
    return _clients['ecs']


def get_ec2_client():
    if 'ec2' not in _clients:
        _clients['ec2'] = boto3.client('ec2')
    return _clients['ec2']


def get_scheduler_client():
    if 'scheduler' not in _clients:
        _clients['scheduler'] = boto3.client('scheduler')
    return _clients['scheduler']


def terminate_ecs_task(task_arn: str) -> bool:
    result = False
    cluster = os.environ.get('ECS_CLUSTER', '')
    if cluster:
        try:
            get_ecs_client().stop_task(cluster=cluster, task=task_arn, reason='Scheduled termination')
            logger.info("Stopped ECS task: %s", task_arn)
            result = True
        except ClientError as e:
            if 'InvalidParameterException' in str(e) or 'TaskNotFound' in str(e):
                logger.info("Task already stopped or not found: %s", task_arn)
                result = True
            else:
                logger.error("Failed to stop ECS task: %s", e)
    return result


def terminate_ec2_instance(instance_id: str) -> bool:
    result = False
    try:
        get_ec2_client().terminate_instances(InstanceIds=[instance_id])
        logger.info("Terminated EC2 instance: %s", instance_id)
        result = True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code in ['InvalidInstanceID.NotFound', 'InvalidInstanceID.Malformed']:
            logger.info("Instance already terminated or not found: %s", instance_id)
            result = True
        else:
            logger.error("Failed to terminate EC2 instance: %s", e)
    return result


def delete_schedule(schedule_name: str):
    try:
        get_scheduler_client().delete_schedule(Name=schedule_name)
        logger.info("Deleted schedule: %s", schedule_name)
    except ClientError as e:
        if 'ResourceNotFoundException' in str(e):
            logger.info("Schedule already deleted: %s", schedule_name)
        else:
            logger.error("Failed to delete schedule: %s", e)


def lambda_handler(event, _context):
    logger.info("Scheduled termination triggered: %s", json.dumps(event))
    resource_type = event.get('resource_type', '')
    resource_id = event.get('resource_id', '')
    schedule_name = event.get('schedule_name', '')
    success = False
    if resource_type == 'ecs_task':
        success = terminate_ecs_task(resource_id)
    elif resource_type == 'ec2_instance':
        success = terminate_ec2_instance(resource_id)
    else:
        logger.error("Unknown resource type: %s", resource_type)
    if schedule_name:
        delete_schedule(schedule_name)
    response = {
        'statusCode': 200 if success else 500,
        'body': json.dumps({'terminated': success, 'resource_type': resource_type, 'resource_id': resource_id})
    }
    return response
