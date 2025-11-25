import boto3
from botocore.exceptions import ClientError


def test_terraform_state_exists(config):
    s3_client = boto3.client('s3', region_name=config['aws_region'])

    try:
        s3_client.head_object(
            Bucket='10ulabs-terraform-state',
            Key='bootstrap/terraform.tfstate'
        )
        state_exists = True
    except ClientError:
        state_exists = False

    assert state_exists
