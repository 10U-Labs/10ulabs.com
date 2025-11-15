import json
import logging
import os
import boto3
from typing import Dict, Any, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')
ssm = boto3.client('ssm')


def launch_packer_builder(config: Dict[str, Any]) -> Dict[str, Any]:
    subnet_ids = os.environ['SUBNETS'].split(',')
    security_group_id = os.environ['SECURITY_GROUPS']
    instance_types = os.environ.get('PACKER_INSTANCE_TYPES', 't4g.large,t4g.medium,t4g.small').split(',')
    iam_instance_profile = os.environ.get('PACKER_INSTANCE_PROFILE', 'PackerEC2InstanceProfile')
    max_price = os.environ.get('PACKER_MAX_PRICE', '0.05')
    vpc_id = os.environ['VPC_ID']

    user_data = f"""#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y curl unzip wget

cd /tmp
wget -q https://releases.hashicorp.com/packer/1.9.4/packer_1.9.4_linux_arm64.zip
unzip packer_1.9.4_linux_arm64.zip
mv packer /usr/local/bin/
chmod +x /usr/local/bin/packer

mkdir -p /opt/packer-build
cd /opt/packer-build

aws s3 cp s3://{os.environ.get('PACKER_CONFIG_BUCKET')}/ami_for_ec2_runners/ . --recursive

packer init template.pkr.hcl
packer build \\
  -var "vpc_id={vpc_id}" \\
  -var "subnet_id={subnet_ids[0]}" \\
  -var "aws_region={os.environ.get('AWS_REGION', 'us-east-1')}" \\
  template.pkr.hcl

INSTANCE_ID=$(ec2-metadata --instance-id | cut -d ' ' -f 2)
aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region {os.environ.get('AWS_REGION', 'us-east-1')}
"""

    response = None
    last_error = None

    for subnet_id in subnet_ids:
        try:
            response = ec2.run_instances(
                ImageId=os.environ.get('BUILDER_AMI_ID'),
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
                        {'Key': 'Name', 'Value': 'packer-ami-builder'},
                        {'Key': 'Type', 'Value': 'ami-builder'},
                        {'Key': 'ManagedBy', 'Value': 'ami-builder-api'}
                    ]
                }]
            )
            logger.info(f"Launched Packer builder instance in subnet {subnet_id}")
            break
        except Exception as e:
            error_msg = str(e)
            if 'InsufficientInstanceCapacity' in error_msg:
                logger.warning(f"No capacity in subnet {subnet_id}, trying next AZ...")
                last_error = e
                continue
            logger.error(f"Error launching Packer builder: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    if response and response['Instances']:
        instance_id = response['Instances'][0]['InstanceId']
        logger.info(f"✅ Launched Packer builder: {instance_id}")
        return {
            'success': True,
            'instance_id': instance_id,
            'message': 'AMI build started'
        }
    else:
        error_detail = str(last_error) if last_error else 'No instances launched'
        logger.error(f"❌ Failed to launch Packer builder: {error_detail}")
        return {
            'success': False,
            'error': error_detail
        }


def list_amis() -> Dict[str, Any]:
    try:
        response = ec2.describe_images(
            Owners=['self'],
            Filters=[
                {'Name': 'tag:Purpose', 'Values': ['github-actions-runner']}
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

        amis.sort(key=lambda x: x['creation_date'], reverse=True)

        logger.info(f"Listed {len(amis)} AMIs")
        return {
            'success': True,
            'amis': amis,
            'count': len(amis)
        }
    except Exception as e:
        logger.error(f"Error listing AMIs: {e}")
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
        logger.info(f"Deregistered AMI: {ami_id}")

        for snapshot_id in snapshot_ids:
            try:
                ec2.delete_snapshot(SnapshotId=snapshot_id)
                logger.info(f"Deleted snapshot: {snapshot_id}")
            except Exception as e:
                logger.warning(f"Failed to delete snapshot {snapshot_id}: {e}")

        return {
            'success': True,
            'ami_id': ami_id,
            'deleted_snapshots': snapshot_ids,
            'message': f'AMI {ami_id} deregistered successfully'
        }
    except Exception as e:
        logger.error(f"Error deregistering AMI {ami_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def lambda_handler(event, context):
    logger.info(f"Received API request: {json.dumps(event)}")

    http_method = event.get('httpMethod', '')
    path = event.get('path', '')

    if http_method == 'POST':
        try:
            if isinstance(event.get('body'), str):
                body = json.loads(event['body'])
            else:
                body = event.get('body', {})

            result = launch_packer_builder(body)

            if result['success']:
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(result)
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(result)
                }
        except Exception as e:
            logger.error(f"Error handling POST request: {e}", exc_info=True)
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': False,
                    'error': 'Internal server error',
                    'details': str(e)
                })
            }

    elif http_method == 'GET':
        result = list_amis()

        if result['success']:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        else:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }

    elif http_method == 'DELETE':
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

        if result['success']:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        else:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }

    else:
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Method not allowed'
            })
        }
