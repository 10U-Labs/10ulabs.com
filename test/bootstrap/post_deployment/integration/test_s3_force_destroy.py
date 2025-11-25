import json
import pytest


def find_tfstate_resource(state, resource_type, resource_name):
    for resource in state['resources']:
        if resource['type'] == resource_type and resource['name'] == resource_name:
            return resource['instances'][0]['attributes']
    return None


@pytest.fixture(name='tfstate')
def tfstate_fixture(s3_client, config):
    response = s3_client.get_object(
        Bucket=config['name_for_terraform_state_bucket'],
        Key='bootstrap/terraform.tfstate'
    )
    return json.loads(response['Body'].read().decode('utf-8'))


@pytest.fixture(name='terraform_state_bucket_attrs')
def terraform_state_bucket_attrs_fixture(tfstate):
    return find_tfstate_resource(tfstate, 'aws_s3_bucket', 'terraform_state')


@pytest.fixture(name='central_logs_bucket_attrs')
def central_logs_bucket_attrs_fixture(tfstate):
    return find_tfstate_resource(tfstate, 'aws_s3_bucket', 'central_logs')


def test_terraform_state_bucket_force_destroy_in_tfstate(terraform_state_bucket_attrs):
    assert terraform_state_bucket_attrs['force_destroy'] is True


def test_central_logs_bucket_force_destroy_in_tfstate(central_logs_bucket_attrs):
    assert central_logs_bucket_attrs['force_destroy'] is True
