"""Integration tests for EC2 runner API endpoint."""
import requests

from ..conftest import (
    make_authenticated_get,
    make_authenticated_post,
)


def test_runner_creation_requires_auth(api_url):
    """Test that runner creation requires authentication."""
    payload = {
        "job_id": 123,
        "github_repo": "any/repo",
        "job_labels": ["ephemeral-ec2-instance"]
    }
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, timeout=10)
    is_forbidden = response.status_code == 403
    assert is_forbidden


def test_ec2_runner_status_requires_auth(api_url):
    """Test that EC2 runner status endpoint requires authentication."""
    response = requests.get(f"{api_url}/v1/ec2-runner", timeout=10)
    is_forbidden = response.status_code == 403
    assert is_forbidden


def test_ec2_runner_status_accepts_valid_api_key(api_url, api_key):
    """Test that EC2 runner status accepts a valid API key."""
    response = make_authenticated_get(f"{api_url}/v1/ec2-runner", api_key, timeout=10)
    is_success = response.status_code == 200
    assert is_success


def test_ec2_runner_status_returns_json(api_url, api_key):
    """Test that EC2 runner status returns JSON content type."""
    response = make_authenticated_get(f"{api_url}/v1/ec2-runner", api_key, timeout=10)
    is_json = response.headers["Content-Type"] == "application/json"
    assert is_json


def test_ec2_runner_status_has_success_field(api_url, api_key):
    """Test that EC2 runner status response has success field."""
    response = make_authenticated_get(f"{api_url}/v1/ec2-runner", api_key, timeout=10)
    has_success = "success" in response.json()
    assert has_success


def test_ec2_runner_status_has_running_instances_field(api_url, api_key):
    """Test that EC2 runner status response has running_instances field."""
    response = make_authenticated_get(f"{api_url}/v1/ec2-runner", api_key, timeout=10)
    has_running_instances = "running_instances" in response.json()
    assert has_running_instances


def test_ec2_runner_status_has_instances_field(api_url, api_key):
    """Test that EC2 runner status response has instances field."""
    response = make_authenticated_get(f"{api_url}/v1/ec2-runner", api_key, timeout=10)
    has_instances = "instances" in response.json()
    assert has_instances


def test_v1_ec2_runner_post_missing_job_id_returns_400(api_url, api_key):
    """Test that POST without job_id returns 400 Bad Request."""
    payload = {"job_labels": ["ephemeral-ec2-instance"], "github_repo": "any/repo"}
    response = make_authenticated_post(
        f"{api_url}/v1/ec2-runner", api_key, json=payload, timeout=10
    )
    is_bad_request = response.status_code == 400
    assert is_bad_request


def test_v1_ec2_runner_post_missing_github_repo_returns_400(api_url, api_key):
    """Test that POST without github_repo returns 400 Bad Request."""
    payload = {"job_id": 333333, "job_labels": ["ephemeral-ec2-instance"]}
    response = make_authenticated_post(
        f"{api_url}/v1/ec2-runner", api_key, json=payload, timeout=10
    )
    is_bad_request = response.status_code == 400
    assert is_bad_request
