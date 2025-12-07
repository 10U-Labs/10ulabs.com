"""End-to-end tests for EC2 runner endpoint."""
import time

import boto3
import pytest
from botocore.exceptions import ClientError

from ..conftest import (
    create_runner_job_payload,
    make_authenticated_get,
    make_authenticated_post,
)


SECONDS_PER_AZ_CAPACITY_CHECK = 19
SECONDS_FOR_SETUP_AND_LAUNCH = 7


def get_ec2_runner_subnet_count():
    """Get the number of subnets configured for EC2 runners."""
    lambda_client = boto3.client('lambda')
    response = lambda_client.get_function_configuration(FunctionName='TenULabsEC2RunnerHandler')
    subnets_env = response.get('Environment', {}).get('Variables', {}).get('SUBNETS', '')
    subnet_count = len(subnets_env.split(',')) if subnets_env else 1
    return subnet_count


def calculate_ec2_runner_timeout():
    """Calculate timeout based on subnet count for AZ capacity checks."""
    subnet_count = get_ec2_runner_subnet_count()
    timeout = SECONDS_FOR_SETUP_AND_LAUNCH + (subnet_count * SECONDS_PER_AZ_CAPACITY_CHECK)
    return timeout


@pytest.fixture(name="latest_ami_exists", scope="module")
def latest_ami_exists_fixture(ec2_client, config):
    """Check if a stable AMI exists for EC2 runners."""
    purpose_tag = config['ec2_runner_ami_purpose_tag']
    purpose_value = config['ec2_runner_ami_purpose_value']
    stable_tag = config['ec2_runner_ami_stable_tag']
    response = ec2_client.describe_images(
        Owners=['self'],
        Filters=[
            {'Name': f'tag:{purpose_tag}', 'Values': [purpose_value]},
            {'Name': f'tag:{stable_tag}', 'Values': ['true']},
            {'Name': 'state', 'Values': ['available']}
        ]
    )
    return len(response['Images']) > 0


def wait_for_instance_running(ec2_client, instance_id, timeout=120):
    """Wait for an EC2 instance to reach the running state."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        state = response['Reservations'][0]['Instances'][0]['State']['Name']
        if state == 'running':
            return True
        if state in ('terminated', 'shutting-down'):
            return False
        time.sleep(5)
    return False


def terminate_instance_safely(ec2_client, instance_id):
    """Terminate an EC2 instance, ignoring errors if already terminated."""
    try:
        ec2_client.terminate_instances(InstanceIds=[instance_id])
    except ClientError:
        pass


def query_workflow_runners_by_run_id(dynamodb_client, table_name, run_id):
    """Query DynamoDB for workflow runners by run ID."""
    response = dynamodb_client.query(
        TableName=table_name,
        KeyConditionExpression='run_id = :rid',
        ExpressionAttributeValues={':rid': {'S': str(run_id)}}
    )
    return response.get('Items', [])


@pytest.fixture(name="test_ec2_runner_instance", scope="module")
def test_ec2_runner_instance_fixture(test_context, latest_ami_exists, ec2_client, config):
    """Create and yield an EC2 runner instance for testing, then terminate it."""
    if not latest_ami_exists:
        yield None
        return
    runner_label = config['ec2_e2e_test']
    job_id, payload = create_runner_job_payload(
        test_context["github_repo"], [runner_label], test_context["github_run_id"]
    )
    response = make_authenticated_post(
        f"{test_context['api_credentials']['url']}/v1/ec2-runner",
        test_context["api_credentials"]["key"],
        json=payload,
        timeout=calculate_ec2_runner_timeout()
    )
    if response.status_code != 200:
        yield None
        return
    instance_id = response.json().get("instance_id")
    if not instance_id:
        yield None
        return
    wait_for_instance_running(ec2_client, instance_id)
    yield {
        "instance_id": instance_id, "job_id": job_id,
        "github_repo": test_context["github_repo"], "run_id": test_context["github_run_id"]
    }
    terminate_instance_safely(ec2_client, instance_id)


def test_ec2_runner_post_returns_response(test_ec2_runner_instance, latest_ami_exists):
    """Test that POST to ec2-runner returns a response."""
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    has_response = test_ec2_runner_instance is not None
    assert has_response


def test_ec2_runner_post_returns_instance_id(test_ec2_runner_instance, latest_ami_exists):
    """Test that POST to ec2-runner returns an instance ID."""
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    has_instance_id = test_ec2_runner_instance.get("instance_id") is not None
    assert has_instance_id


def test_ec2_runner_instance_reaches_running_state(
    test_ec2_runner_instance, ec2_client, latest_ami_exists
):
    """Test that the EC2 runner instance reaches the running state."""
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    state = response['Reservations'][0]['Instances'][0]['State']['Name']
    is_running = state == 'running'
    assert is_running


def test_ec2_runner_instance_has_type_tag(
    test_ec2_runner_instance, ec2_client, latest_ami_exists
):
    """Test that the EC2 runner instance has the Type tag set correctly."""
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
    tag_dict = {tag['Key']: tag['Value'] for tag in tags}
    has_correct_type = tag_dict.get("Type") == "workflow-runner"
    assert has_correct_type


def test_ec2_runner_instance_has_managed_by_tag(
    test_ec2_runner_instance, ec2_client, latest_ami_exists
):
    """Test that the EC2 runner instance has the ManagedBy tag set correctly."""
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
    tag_dict = {tag['Key']: tag['Value'] for tag in tags}
    has_correct_managed_by = tag_dict.get("ManagedBy") == "api-ec2-runner"
    assert has_correct_managed_by


def test_ec2_runner_instance_has_job_id_tag(
    test_ec2_runner_instance, ec2_client, latest_ami_exists
):
    """Test that the EC2 runner instance has the GitHubJobId tag set correctly."""
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    job_id = test_ec2_runner_instance.get("job_id")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
    tag_dict = {tag['Key']: tag['Value'] for tag in tags}
    has_correct_job_id = tag_dict.get("GitHubJobId") == str(job_id)
    assert has_correct_job_id


def test_ec2_runner_instance_has_repo_tag(
    test_ec2_runner_instance, ec2_client, latest_ami_exists
):
    """Test that the EC2 runner instance has the GitHubRepo tag set correctly."""
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    github_repo = test_ec2_runner_instance.get("github_repo")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
    tag_dict = {tag['Key']: tag['Value'] for tag in tags}
    has_correct_repo = tag_dict.get("GitHubRepo") == github_repo
    assert has_correct_repo


def test_ec2_runner_appears_in_status_endpoint(
    test_ec2_runner_instance, api_url, api_key, latest_ami_exists
):
    """Test that the EC2 runner appears in the status endpoint."""
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    status_response = make_authenticated_get(f"{api_url}/v1/ec2-runner", api_key, timeout=10)
    instances = status_response.json().get("instances", [])
    instance_ids = [inst.get("instance_id") for inst in instances]
    is_in_list = instance_id in instance_ids
    assert is_in_list


def test_ec2_runner_instance_enforces_imdsv2(
    test_ec2_runner_instance, ec2_client, latest_ami_exists
):
    """Test that the EC2 runner instance enforces IMDSv2."""
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    metadata_options = response['Reservations'][0]['Instances'][0].get('MetadataOptions', {})
    requires_tokens = metadata_options.get("HttpTokens") == "required"
    assert requires_tokens


def test_ec2_runner_instance_has_run_id_tag(
    test_ec2_runner_instance, ec2_client, latest_ami_exists
):
    """Test that the EC2 runner instance has the RunId tag set correctly."""
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    run_id = test_ec2_runner_instance.get("run_id")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
    tag_dict = {tag['Key']: tag['Value'] for tag in tags}
    has_correct_run_id = tag_dict.get("RunId") == str(run_id)
    assert has_correct_run_id


def test_ec2_runner_stored_in_dynamodb(
    test_ec2_runner_instance, dynamodb_client, workflow_runners_table_name, latest_ami_exists
):
    """Test that the EC2 runner is stored in DynamoDB."""
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    run_id = test_ec2_runner_instance.get("run_id")
    items = query_workflow_runners_by_run_id(dynamodb_client, workflow_runners_table_name, run_id)
    has_items = len(items) > 0
    assert has_items
