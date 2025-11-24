import boto3
from botocore.exceptions import ClientError
import pytest


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(tfvars):
    return f"https://{tfvars['domain_subdomain']}"


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture(tfvars):
    region = tfvars.get('aws_region', 'us-east-1')
    client = boto3.client('ssm', region_name=region)
    param_response = client.get_parameter(Name='/api/key', WithDecryption=True)
    return param_response['Parameter']['Value'] if param_response else None


@pytest.fixture(name="ecr_image_count", scope="module")
def ecr_image_count_fixture(tfvars):
    region = tfvars.get('aws_region', 'us-east-1')
    ecr_client = boto3.client('ecr', region_name=region)
    try:
        response = ecr_client.describe_images(
            repositoryName='github-runner',
            filter={'tagStatus': 'TAGGED'}
        )
        stable_images = [
            img for img in response.get('imageDetails', [])
            if 'stable' in img.get('imageTags', [])
        ]
        return len(stable_images)
    except ClientError:
        return 0
