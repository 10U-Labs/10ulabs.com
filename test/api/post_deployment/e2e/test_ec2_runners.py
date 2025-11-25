import time
import pytest
import requests
from botocore.exceptions import ClientError
from .conftest import make_authenticated_post, make_authenticated_get


@pytest.fixture(name="latest_ami_exists", scope="module")
def latest_ami_exists_fixture(ec2_client):
    response = ec2_client.describe_images(
        Owners=['self'],
        Filters=[
            {'Name': 'tag:Purpose', 'Values': ['Github self-hosted EC2 runner']},
            {'Name': 'tag:stable', 'Values': ['true']},
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
    job_id = int(time.time())
    payload = {
        "job_id": job_id,
        "job_labels": ["ephemeral-ec2-spot-instance"],
        "github_repo": github_repo
    }
    response = make_authenticated_post(
        f"{api_url}/v1/ec2-runner", api_key, json=payload
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


def test_protected_endpoint_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners/latest", timeout=10)
    assert response.status_code == 403


def test_protected_endpoint_rejects_invalid_api_key(api_url):
    headers = {"x-api-key": "invalid-key-12345"}
    url = f"{api_url}/v1/image-for-ec2-runners/latest"
    response = requests.get(url, headers=headers, timeout=10)
    assert response.status_code == 403


def test_protected_endpoint_accepts_valid_api_key(api_url, api_key, latest_ami_exists):
    if not latest_ami_exists:
        pytest.skip("No AMI available")
    response = make_authenticated_get(f"{api_url}/v1/image-for-ec2-runners/latest", api_key)
    assert response.status_code == 200


def test_ec2_runner_list_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners", timeout=10)
    assert response.status_code == 403


def test_runner_creation_requires_auth(api_url):
    payload = {
        "job_id": 123,
        "github_repo": "any/repo",
        "job_labels": ["ephemeral-ec2-spot-instance"]
    }
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, timeout=10)
    assert response.status_code == 403


def test_ec2_runner_status_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/ec2-runner", timeout=10)
    assert response.status_code == 403


def test_ec2_runner_status_accepts_valid_api_key(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/ec2-runner", api_key)
    assert response.status_code == 200


def test_ec2_runner_status_returns_json(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/ec2-runner", api_key)
    assert response.headers["Content-Type"] == "application/json"


def test_ec2_runner_status_has_success_field(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/ec2-runner", api_key)
    assert "success" in response.json()


def test_ec2_runner_status_has_running_instances_field(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/ec2-runner", api_key)
    assert "running_instances" in response.json()


def test_ec2_runner_status_has_instances_field(api_url, api_key):
    response = make_authenticated_get(f"{api_url}/v1/ec2-runner", api_key)
    assert "instances" in response.json()


def test_v1_ec2_runner_post_missing_job_id_returns_400(api_url, api_key):
    payload = {"job_labels": ["ephemeral-ec2-spot-instance"], "github_repo": "any/repo"}
    response = make_authenticated_post(f"{api_url}/v1/ec2-runner", api_key, json=payload)
    assert response.status_code == 400


def test_v1_ec2_runner_post_missing_github_repo_returns_400(api_url, api_key):
    payload = {"job_id": 333333, "job_labels": ["ephemeral-ec2-spot-instance"]}
    response = make_authenticated_post(f"{api_url}/v1/ec2-runner", api_key, json=payload)
    assert response.status_code == 400


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
    status_response = make_authenticated_get(f"{api_url}/v1/ec2-runner", api_key)
    instances = status_response.json().get("instances", [])
    instance_ids = [inst.get("instance_id") for inst in instances]
    assert instance_id in instance_ids
