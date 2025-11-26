from test.api.post_deployment.conftest import (
    create_runner_job_payload,
    make_e2e_get,
    make_e2e_post,
)
import time
import pytest
from botocore.exceptions import ClientError


@pytest.fixture(name="latest_ami_exists", scope="module")
def latest_ami_exists_fixture(ec2_client, config):
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
    try:
        ec2_client.terminate_instances(InstanceIds=[instance_id])
    except ClientError:
        pass


@pytest.fixture(name="test_ec2_runner_instance", scope="module")
def test_ec2_runner_instance_fixture(
    api_url, api_key, github_repo, latest_ami_exists, ec2_client
):
    if not latest_ami_exists:
        yield None
        return
    job_id, payload = create_runner_job_payload(github_repo, ["ephemeral-ec2-spot-instance"])
    response = make_e2e_post(
        f"{api_url}/v1/ec2-runner", api_key, json=payload, timeout=30
    )
    if response.status_code != 200:
        yield None
        return
    data = response.json()
    instance_id = data.get("instance_id")
    if not instance_id:
        yield None
        return
    wait_for_instance_running(ec2_client, instance_id)
    yield {"instance_id": instance_id, "job_id": job_id, "github_repo": github_repo}
    terminate_instance_safely(ec2_client, instance_id)


def test_ec2_runner_post_returns_instance_id(test_ec2_runner_instance, latest_ami_exists):
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    assert test_ec2_runner_instance is not None
    assert test_ec2_runner_instance.get("instance_id") is not None


def test_ec2_runner_instance_reaches_running_state(
    test_ec2_runner_instance, ec2_client, latest_ami_exists
):
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    state = response['Reservations'][0]['Instances'][0]['State']['Name']
    assert state == 'running'


def test_ec2_runner_instance_has_type_tag(
    test_ec2_runner_instance, ec2_client, latest_ami_exists
):
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
    tag_dict = {tag['Key']: tag['Value'] for tag in tags}
    assert tag_dict.get("Type") == "ephemeral-runner"


def test_ec2_runner_instance_has_managed_by_tag(
    test_ec2_runner_instance, ec2_client, latest_ami_exists
):
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
    tag_dict = {tag['Key']: tag['Value'] for tag in tags}
    assert tag_dict.get("ManagedBy") == "api-ec2-spot-runner"


def test_ec2_runner_instance_has_job_id_tag(
    test_ec2_runner_instance, ec2_client, latest_ami_exists
):
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    job_id = test_ec2_runner_instance.get("job_id")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
    tag_dict = {tag['Key']: tag['Value'] for tag in tags}
    assert tag_dict.get("GitHubJobId") == str(job_id)


def test_ec2_runner_instance_has_repo_tag(
    test_ec2_runner_instance, ec2_client, latest_ami_exists
):
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    github_repo = test_ec2_runner_instance.get("github_repo")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
    tag_dict = {tag['Key']: tag['Value'] for tag in tags}
    assert tag_dict.get("GitHubRepo") == github_repo


def test_ec2_runner_appears_in_status_endpoint(
    test_ec2_runner_instance, api_url, api_key, latest_ami_exists
):
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    status_response = make_e2e_get(f"{api_url}/v1/ec2-runner", api_key)
    instances = status_response.json().get("instances", [])
    instance_ids = [inst.get("instance_id") for inst in instances]
    assert instance_id in instance_ids


def test_ec2_runner_instance_enforces_imdsv2(
    test_ec2_runner_instance, ec2_client, latest_ami_exists
):
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    if test_ec2_runner_instance is None:
        pytest.fail("Test instance not created")
    instance_id = test_ec2_runner_instance.get("instance_id")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    metadata_options = response['Reservations'][0]['Instances'][0].get('MetadataOptions', {})
    assert metadata_options.get("HttpTokens") == "required"
