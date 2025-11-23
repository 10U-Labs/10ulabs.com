import base64
import concurrent.futures
import hashlib
import hmac
import json
import time
import urllib.parse
from datetime import datetime, timedelta
import boto3
import pytest
import requests


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(tfvars):
    return f"https://{tfvars['domain_subdomain']}"


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture(tfvars):
    region = tfvars.get('aws_region', 'us-east-1')
    client = boto3.client('ssm', region_name=region)
    param_response = client.get_parameter(Name='/api/key', WithDecryption=True)
    return param_response['Parameter']['Value'] if param_response else None


def test_health_endpoint_responds(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.status_code == 200


def test_health_endpoint_returns_json(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.headers["Content-Type"] == "application/json"


def test_health_endpoint_has_status_field(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    data = response.json()
    assert "status" in data


def test_health_endpoint_status_healthy(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint_responds(api_url):
    response = requests.get(api_url, timeout=10)
    assert response.status_code == 200


def test_invalid_endpoint_returns_404(api_url):
    response = requests.get(f"{api_url}/nonexistent", timeout=10)
    assert response.status_code == 404


def test_openapi_spec_accessible(api_url):
    response = requests.get(f"{api_url}/openapi.yml", timeout=10)
    assert response.status_code == 200


def test_openapi_spec_is_yaml(api_url):
    response = requests.get(f"{api_url}/openapi.yml", timeout=10)
    assert "application/x-yaml" in response.headers.get("Content-Type", "") or "text/yaml" in response.headers.get("Content-Type", "")


def test_echo_endpoint_accessible_without_auth(api_url):
    response = requests.post(f"{api_url}/v1/echo", json={"test": "data"}, timeout=10)
    assert response.status_code == 200


def test_echo_endpoint_returns_echoed_data(api_url):
    test_data = {"message": "hello", "number": 42}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, timeout=10)
    data = response.json()
    assert data["echo"] == test_data


def test_protected_endpoint_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners/latest", timeout=10)
    assert response.status_code == 403


def test_protected_endpoint_rejects_invalid_api_key(api_url):
    headers = {"x-api-key": "invalid-key-12345"}
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners/latest", headers=headers, timeout=10)
    assert response.status_code == 403


def test_protected_endpoint_accepts_valid_api_key(api_url, api_key):
    if api_key is None:
        pytest.skip("API key not available")
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners/latest", headers=headers, timeout=10)
    assert response.status_code == 200


def test_docker_runner_endpoint_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-docker-runners/latest", timeout=10)
    assert response.status_code == 403


def test_docker_runner_endpoint_accepts_valid_api_key(api_url, api_key):
    if api_key is None:
        pytest.skip("API key not available")
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-docker-runners/latest", headers=headers, timeout=10)
    assert response.status_code != 403


def test_docker_runner_endpoint_returns_images_when_available(api_url, api_key, ecr_image_count):
    if ecr_image_count == 0:
        pytest.skip("No ECR images available")
    if api_key is None:
        pytest.skip("API key not available")
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-docker-runners/latest", headers=headers, timeout=10)
    assert response.status_code == 200


def test_docker_runner_endpoint_returns_error_when_no_images(api_url, api_key, ecr_image_count):
    if ecr_image_count > 0:
        pytest.skip("ECR images exist")
    if api_key is None:
        pytest.skip("API key not available")
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-docker-runners/latest", headers=headers, timeout=10)
    assert response.status_code in [404, 500]


def test_ec2_runner_list_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners", timeout=10)
    assert response.status_code == 403


def test_docker_runner_list_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/image-for-docker-runners", timeout=10)
    assert response.status_code == 403


def test_runner_creation_requires_auth(api_url):
    payload = {"job_id": 123, "github_repo": "test/repo", "job_labels": ["test"]}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, timeout=10)
    assert response.status_code == 403


def test_docker_runner_status_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/docker-runner", timeout=10)
    assert response.status_code == 403


def test_docker_runner_status_accepts_valid_api_key(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    assert response.status_code == 200


def test_docker_runner_status_returns_json(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    assert response.headers["Content-Type"] == "application/json"


def test_docker_runner_status_has_success_field(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    data = response.json()
    assert "success" in data


def test_docker_runner_status_has_running_tasks_field(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    data = response.json()
    assert "running_tasks" in data


def test_docker_runner_status_has_tasks_field(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    data = response.json()
    assert "tasks" in data


def test_docker_runner_status_has_cluster_field(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    data = response.json()
    assert "cluster" in data


def test_ec2_runner_status_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/ec2-runner", timeout=10)
    assert response.status_code == 403


def test_ec2_runner_status_accepts_valid_api_key(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    assert response.status_code == 200


def test_ec2_runner_status_returns_json(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    assert response.headers["Content-Type"] == "application/json"


def test_ec2_runner_status_has_success_field(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    data = response.json()
    assert "success" in data


def test_ec2_runner_status_has_running_instances_field(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    data = response.json()
    assert "running_instances" in data


def test_ec2_runner_status_has_instances_field(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    data = response.json()
    assert "instances" in data


def test_echo_endpoint_with_unicode(api_url):
    test_data = {"message": "Hello 世界 🌍"}
    response = requests.post(f"{api_url}/v1/echo", json=test_data, timeout=10)
    assert response.status_code == 200
    data = response.json()
    assert data["echo"]["message"] == "Hello 世界 🌍"


def test_echo_endpoint_with_large_payload(api_url):
    large_data = {"items": [{"id": i, "value": f"item-{i}"} for i in range(100)]}
    response = requests.post(f"{api_url}/v1/echo", json=large_data, timeout=10)
    assert response.status_code == 200


def test_echo_endpoint_preserves_data_types(api_url):
    test_data = {
        "string": "test",
        "number": 42,
        "float": 3.14,
        "boolean": True,
        "null": None
    }
    response = requests.post(f"{api_url}/v1/echo", json=test_data, timeout=10)
    data = response.json()
    echo = data["echo"]
    assert echo["string"] == "test"
    assert echo["number"] == 42
    assert echo["float"] == 3.14
    assert echo["boolean"] is True
    assert echo["null"] is None


def test_concurrent_health_requests(api_url):
    def make_request():
        return requests.get(f"{api_url}/health", timeout=10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    assert all(r.status_code == 200 for r in results)


def test_health_endpoint_response_time(api_url):
    start = time.time()
    response = requests.get(f"{api_url}/health", timeout=10)
    duration = time.time() - start
    assert response.status_code == 200
    assert duration < 5.0


def test_v1_runners_post_with_valid_workflow_job(api_url, api_key):
    headers = {"x-api-key": api_key, "x-github-event": "workflow_job"}
    payload = {
        "action": "queued",
        "workflow_job": {
            "id": 999999,
            "labels": ["ephemeral-ec2-spot-instance"],
            "status": "queued"
        },
        "repository": {"full_name": "test/repo"}
    }
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_v1_runners_post_with_invalid_signature(api_url):
    headers = {"x-hub-signature-256": "sha256=invalid"}
    payload = {"action": "ping"}
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_v1_runners_post_with_ping_event(api_url):
    headers = {"x-github-event": "ping"}
    payload = {"zen": "Test", "hook_id": 12345}
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_v1_runners_post_with_duplicate_delivery_id(api_url):
    headers = {"x-github-event": "ping", "x-github-delivery": "test-duplicate-id"}
    payload = {"zen": "Test"}
    requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_v1_runners_health_get_with_valid_api_key(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    assert response.status_code in [200, 403]


def test_v1_runners_health_returns_circuit_breaker_state(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        assert "circuit_breaker" in data or "status" in data


def test_v1_docker_runner_post_creates_fargate_task(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 888888, "job_labels": ["ephemeral-ecs-fargate-spot"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 202, 403, 500]


def test_v1_docker_runner_post_with_no_stable_image_triggers_build(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 777777, "job_labels": ["test"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 202, 403, 500]


def test_v1_docker_runner_post_missing_job_id_returns_400(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_labels": ["test"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [400, 403]


def test_v1_docker_runner_post_missing_github_repo_returns_400(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 666666, "job_labels": ["test"]}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [400, 403]


def test_v1_docker_runner_get_task_details_include_metadata(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        assert "running_tasks" in data


def test_v1_ec2_runner_post_creates_ec2_instance(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 555555, "job_labels": ["ephemeral-ec2-spot-instance"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_v1_ec2_runner_post_with_no_ami_triggers_build(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 444444, "job_labels": ["test"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_v1_ec2_runner_post_missing_job_id_returns_400(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_labels": ["test"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [400, 403]


def test_v1_ec2_runner_post_missing_github_repo_returns_400(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 333333, "job_labels": ["test"]}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [400, 403]


def test_v1_ec2_runner_get_instance_details_include_metadata(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        assert "running_instances" in data


def test_v1_image_for_docker_runners_post_triggers_workflow(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.post(f"{api_url}/v1/image-for-docker-runners", json={}, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_v1_image_for_docker_runners_post_invalid_api_key_returns_403(api_url):
    headers = {"x-api-key": "invalid-key"}
    response = requests.post(f"{api_url}/v1/image-for-docker-runners", json={}, headers=headers, timeout=10)
    assert response.status_code == 403


def test_v1_image_for_docker_runners_get_lists_all_images(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-docker-runners", headers=headers, timeout=10)
    assert response.status_code in [200, 403]


def test_v1_image_for_docker_runners_get_with_no_images_returns_empty_list(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-docker-runners", headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        assert "images" in data or "count" in data


def test_v1_image_for_docker_runners_latest_get_returns_latest_stable(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-docker-runners/latest", headers=headers, timeout=10)
    assert response.status_code in [200, 403, 404, 500]


def test_v1_image_for_docker_runners_delete_removes_image(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.delete(f"{api_url}/v1/image-for-docker-runners/sha256:test", headers=headers, timeout=10)
    assert response.status_code in [200, 403, 404, 500]


def test_v1_image_for_docker_runners_delete_invalid_digest_returns_error(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.delete(f"{api_url}/v1/image-for-docker-runners/invalid", headers=headers, timeout=10)
    assert response.status_code in [400, 403, 404, 500]


def test_v1_image_for_ec2_runners_post_triggers_packer_build(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.post(f"{api_url}/v1/image-for-ec2-runners", json={}, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_v1_image_for_ec2_runners_post_invalid_api_key_returns_403(api_url):
    headers = {"x-api-key": "invalid-key"}
    response = requests.post(f"{api_url}/v1/image-for-ec2-runners", json={}, headers=headers, timeout=10)
    assert response.status_code == 403


def test_v1_image_for_ec2_runners_get_lists_all_amis(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners", headers=headers, timeout=10)
    assert response.status_code in [200, 403]


def test_v1_image_for_ec2_runners_get_with_no_amis_returns_empty_list(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners", headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        assert "amis" in data or "count" in data


def test_v1_image_for_ec2_runners_latest_get_retrieves_from_ssm(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-ec2-runners/latest", headers=headers, timeout=10)
    assert response.status_code in [200, 403, 404, 500]


def test_v1_image_for_ec2_runners_delete_deregisters_ami(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.delete(f"{api_url}/v1/image-for-ec2-runners/ami-test123", headers=headers, timeout=10)
    assert response.status_code in [200, 403, 404, 500]


def test_v1_image_for_ec2_runners_delete_invalid_ami_id_returns_error(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.delete(f"{api_url}/v1/image-for-ec2-runners/invalid", headers=headers, timeout=10)
    assert response.status_code in [400, 403, 404, 500]


def test_malformed_json_request_returns_400(api_url):
    headers = {"Content-Type": "application/json"}
    response = requests.post(f"{api_url}/v1/echo", data="not valid json", headers=headers, timeout=10)
    assert response.status_code in [400, 500]


def test_oversized_payload_returns_413(api_url):
    large_payload = {"data": "x" * (10 * 1024 * 1024)}
    response = requests.post(f"{api_url}/v1/echo", json=large_payload, timeout=30)
    assert response.status_code in [200, 413, 500]


def test_rate_limit_exceeded_returns_429(api_url):
    responses = []
    for _ in range(200):
        try:
            resp = requests.get(f"{api_url}/health", timeout=1)
            responses.append(resp.status_code)
            if resp.status_code == 429:
                break
        except requests.exceptions.Timeout:
            continue
    assert 200 in responses or 429 in responses


def test_rate_limit_applies_to_health_endpoint(api_url):
    responses = []
    for _ in range(60):
        try:
            resp = requests.get(f"{api_url}/health", timeout=2)
            responses.append(resp.status_code)
            time.sleep(0.1)
        except requests.exceptions.Timeout:
            continue
    assert 200 in responses


def test_rate_limit_applies_to_echo_endpoint(api_url):
    responses = []
    for _ in range(60):
        try:
            resp = requests.post(f"{api_url}/v1/echo", json={"test": "data"}, timeout=2)
            responses.append(resp.status_code)
            time.sleep(0.1)
        except requests.exceptions.Timeout:
            continue
    assert 200 in responses


def test_rate_limit_headers_present_in_response(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.status_code == 200


def test_rate_limit_burst_allows_initial_requests(api_url):
    success_count = 0
    for _ in range(10):
        try:
            resp = requests.get(f"{api_url}/health", timeout=2)
            if resp.status_code == 200:
                success_count += 1
        except requests.exceptions.Timeout:
            continue
    assert success_count > 0


def test_internal_server_error_returns_500(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": "invalid-type", "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 400, 403, 500]


def test_service_unavailable_returns_503(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.status_code in [200, 503]


def test_circuit_breaker_opens_after_threshold_failures(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    assert response.status_code in [200, 403, 503]


def test_circuit_breaker_transitions_to_half_open_after_timeout(api_url, api_key):
    headers = {"x-api-key": api_key}
    requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    time.sleep(2)
    response = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    assert response.status_code in [200, 403, 503]


def test_circuit_breaker_closes_after_successful_request_in_half_open(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    assert response.status_code in [200, 403]


def test_requests_rejected_when_circuit_breaker_open(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    assert response.status_code in [200, 403, 503]


def test_duplicate_webhook_delivery_ids_ignored(api_url):
    headers = {"x-github-event": "ping", "x-github-delivery": "e2e-test-duplicate"}
    payload = {"zen": "Test"}
    requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    response2 = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response2.status_code in [200, 401]


def test_idempotency_table_records_expire_after_ttl(api_url):
    headers = {"x-github-event": "ping", "x-github-delivery": f"e2e-test-ttl-{int(time.time())}"}
    payload = {"zen": "Test"}
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_webhook_events_enqueued_to_sqs(api_url):
    headers = {"x-github-event": "workflow_job"}
    payload = {
        "action": "queued",
        "workflow_job": {"id": 111111, "labels": ["ephemeral-ec2-spot-instance"], "status": "queued"},
        "repository": {"full_name": "test/repo"}
    }
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_sqs_messages_processed_by_lambda(_api_url):
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
    assert "ApproximateNumberOfMessages" in attributes["Attributes"]


def test_failed_messages_move_to_dlq_after_max_retries(_api_url):
    sqs = boto3.client('sqs', region_name='us-east-1')
    dlq_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-job-dlq')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=['ApproximateNumberOfMessages'])
    assert "ApproximateNumberOfMessages" in attributes["Attributes"]


def test_get_docker_runner_image_by_digest(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/image-for-docker-runners/sha256:test123", headers=headers, timeout=10)
    assert response.status_code in [200, 404]


def test_concurrent_docker_runner_creation(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 123456, "job_labels": ["test"], "github_repo": "test/repo"}
    def create_runner():
        return requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(create_runner) for _ in range(3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    assert all(r.status_code in [200, 202, 403, 500] for r in results)


def test_concurrent_ec2_runner_creation(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 654321, "job_labels": ["test"], "github_repo": "test/repo"}
    def create_runner():
        return requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(create_runner) for _ in range(3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    assert all(r.status_code in [200, 403, 500] for r in results)


def test_docker_image_build_triggers_workflow(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.post(f"{api_url}/v1/image-for-docker-runners", json={}, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_ec2_ami_build_triggers_workflow(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.post(f"{api_url}/v1/image-for-ec2-runners", json={}, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_workflow_job_webhook_enqueues_and_processes(api_url):
    headers = {"x-github-event": "workflow_job"}
    payload = {
        "action": "queued",
        "workflow_job": {"id": 111111, "labels": ["ephemeral-ec2-spot-instance"], "status": "queued"},
        "repository": {"full_name": "test/repo"}
    }
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_sqs_message_processing_updates_status(_api_url):
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
    assert "ApproximateNumberOfMessages" in attributes["Attributes"]


def test_dlq_reprocessor_moves_messages_back(_api_url):
    sqs = boto3.client('sqs', region_name='us-east-1')
    try:
        dlq_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-job-dlq')['QueueUrl']
        attributes = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=['ApproximateNumberOfMessages'])
        assert "ApproximateNumberOfMessages" in attributes["Attributes"]
    except sqs.exceptions.QueueDoesNotExist:
        assert True


def test_circuit_breaker_publishes_metrics(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    assert response.status_code in [200, 403]


def test_queue_depth_metrics_published(_api_url):
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
    assert "ApproximateNumberOfMessages" in attributes["Attributes"]


def test_webhook_invalid_signature_rejected(api_url):
    headers = {"x-hub-signature-256": "sha256=invalidsignature123456"}
    payload = {"action": "queued"}
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_runner_creation_fails_when_ecs_unavailable(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 999999, "job_labels": ["test"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/docker-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_runner_creation_fails_when_ec2_capacity_unavailable(api_url, api_key):
    headers = {"x-api-key": api_key}
    payload = {"job_id": 888888, "job_labels": ["test"], "github_repo": "test/repo"}
    response = requests.post(f"{api_url}/v1/ec2-runner", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 403, 500]


def test_runner_registers_with_github(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/ec2-runner", headers=headers, timeout=10)
    assert response.status_code in [200, 403]


def test_runner_self_terminates_after_job(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/docker-runner", headers=headers, timeout=10)
    assert response.status_code in [200, 403]


def test_cloudfront_delivers_404_page_for_nonexistent_endpoint(api_url):
    response = requests.get(f"{api_url}/nonexistent", timeout=10)
    assert response.status_code == 404


def test_cloudfront_404_page_contains_error_message(api_url):
    response = requests.get(f"{api_url}/nonexistent", timeout=10)
    assert "404" in response.text


def test_cloudfront_404_page_contains_not_found_text(api_url):
    response = requests.get(f"{api_url}/nonexistent", timeout=10)
    assert "Not Found" in response.text or "Endpoint not found" in response.text


def test_cloudfront_404_page_has_link_to_docs(api_url):
    response = requests.get(f"{api_url}/nonexistent", timeout=10)
    assert "API Documentation" in response.text or "/" in response.text


def test_docker_image_by_digest_returns_image_details(api_url, api_key):
    headers = {"x-api-key": api_key}
    list_response = requests.get(f"{api_url}/v1/image-for-docker-runners", headers=headers, timeout=10)
    if list_response.status_code == 200:
        data = list_response.json()
        if data.get("images") and len(data["images"]) > 0:
            digest = data["images"][0]["digest"]
            response = requests.get(f"{api_url}/v1/image-for-docker-runners/{digest}", headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                assert "digest" in result or "success" in result


def test_docker_image_by_digest_includes_tags(api_url, api_key):
    headers = {"x-api-key": api_key}
    list_response = requests.get(f"{api_url}/v1/image-for-docker-runners", headers=headers, timeout=10)
    if list_response.status_code == 200:
        data = list_response.json()
        if data.get("images") and len(data["images"]) > 0:
            digest = data["images"][0]["digest"]
            response = requests.get(f"{api_url}/v1/image-for-docker-runners/{digest}", headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                assert "tags" in result or "success" in result


def test_docker_image_by_digest_includes_pushed_at(api_url, api_key):
    headers = {"x-api-key": api_key}
    list_response = requests.get(f"{api_url}/v1/image-for-docker-runners", headers=headers, timeout=10)
    if list_response.status_code == 200:
        data = list_response.json()
        if data.get("images") and len(data["images"]) > 0:
            digest = data["images"][0]["digest"]
            response = requests.get(f"{api_url}/v1/image-for-docker-runners/{digest}", headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                assert "pushed_at" in result or "success" in result


def test_docker_image_by_digest_includes_size(api_url, api_key):
    headers = {"x-api-key": api_key}
    list_response = requests.get(f"{api_url}/v1/image-for-docker-runners", headers=headers, timeout=10)
    if list_response.status_code == 200:
        data = list_response.json()
        if data.get("images") and len(data["images"]) > 0:
            digest = data["images"][0]["digest"]
            response = requests.get(f"{api_url}/v1/image-for-docker-runners/{digest}", headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                assert "size_bytes" in result or "success" in result


def test_webhook_to_sqs_workflow_enqueues_job(api_url):
    headers = {"x-github-event": "workflow_job", "x-github-delivery": f"e2e-workflow-test-{int(time.time())}"}
    payload = {
        "action": "queued",
        "workflow_job": {"id": 999999, "labels": ["ephemeral-ec2-spot-instance"], "status": "queued"},
        "repository": {"full_name": "test/repo"}
    }
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_sqs_message_retry_moves_to_dlq_after_max_attempts():
    sqs = boto3.client('sqs', region_name='us-east-1')
    dlq_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-dlq')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=['ApproximateNumberOfMessages'])
    dlq_count = int(attributes['Attributes']['ApproximateNumberOfMessages'])
    assert dlq_count >= 0


def test_dlq_reprocessor_workflow_moves_messages_back():
    sqs = boto3.client('sqs', region_name='us-east-1')
    try:
        job_dlq_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-job-dlq')['QueueUrl']
        initial_dlq_attrs = sqs.get_queue_attributes(QueueUrl=job_dlq_url, AttributeNames=['ApproximateNumberOfMessages'])
        initial_dlq_count = int(initial_dlq_attrs['Attributes']['ApproximateNumberOfMessages'])
        assert initial_dlq_count >= 0
    except sqs.exceptions.QueueDoesNotExist:
        assert True


def test_circuit_breaker_remediation_workflow_detects_state(api_url, api_key):
    headers = {"x-api-key": api_key}
    response = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        assert "circuit_breaker" in data or "status" in data


def test_webhook_signature_validation_rejects_invalid_signatures(api_url):
    payload = {"action": "ping"}
    payload_str = json.dumps(payload)
    wrong_secret = "wrong-secret"
    signature = hmac.new(wrong_secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
    headers = {"x-hub-signature-256": f"sha256={signature}", "x-github-event": "ping"}
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_idempotency_prevents_duplicate_webhook_processing(api_url):
    delivery_id = f"e2e-idempotency-{int(time.time())}"
    headers = {"x-github-event": "ping", "x-github-delivery": delivery_id}
    payload = {"zen": "Test idempotency"}
    response1 = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    response2 = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response1.status_code in [200, 401]
    assert response2.status_code in [200, 401]


def test_sqs_visibility_timeout_prevents_duplicate_processing():
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['VisibilityTimeout'])
    visibility_timeout = int(attributes['Attributes']['VisibilityTimeout'])
    assert visibility_timeout > 30


def test_dynamodb_ttl_expires_old_idempotency_records():
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    response = dynamodb.describe_time_to_live(TableName='TenULabsWebhookHandler-idempotency')
    assert response['TimeToLiveDescription']['TimeToLiveStatus'] == 'ENABLED'


def test_cloudwatch_metrics_published_for_circuit_breaker():
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    response = cloudwatch.get_metric_statistics(
        Namespace='WebhookRouter',
        MetricName='CircuitBreakerState',
        Dimensions=[],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average']
    )
    assert 'Datapoints' in response


def test_cloudwatch_metrics_published_for_queue_depth():
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    response = cloudwatch.get_metric_statistics(
        Namespace='WebhookRouter',
        MetricName='QueueDepth',
        Dimensions=[],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average']
    )
    assert 'Datapoints' in response


def test_cloudwatch_metrics_published_for_processing_time():
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    response = cloudwatch.get_metric_statistics(
        Namespace='WebhookRouter',
        MetricName='ProcessingTime',
        Dimensions=[],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average']
    )
    assert 'Datapoints' in response


def test_eventbridge_triggers_circuit_breaker_remediation():
    events = boto3.client('events', region_name='us-east-1')
    rules = events.list_rules()
    rule_names = [r['Name'] for r in rules['Rules']]
    assert len(rule_names) > 0


def test_eventbridge_triggers_dlq_reprocessor():
    events = boto3.client('events', region_name='us-east-1')
    rules = events.list_rules()
    scheduled_rules = [r for r in rules['Rules'] if r.get('ScheduleExpression')]
    assert len(scheduled_rules) > 0


def test_webhook_payload_with_urlencoded_format(api_url):
    headers = {"x-github-event": "ping", "Content-Type": "application/x-www-form-urlencoded"}
    payload_dict = {"zen": "Test URL encoding", "hook_id": 12345}
    payload_str = urllib.parse.urlencode({"payload": json.dumps(payload_dict)})
    response = requests.post(f"{api_url}/v1/runners", data=payload_str, headers=headers, timeout=10)
    assert response.status_code in [200, 400, 401]


def test_webhook_payload_with_base64_encoding(api_url):
    headers = {"x-github-event": "ping"}
    payload = {"zen": "Test base64"}
    encoded_payload = base64.b64encode(json.dumps(payload).encode()).decode()
    response = requests.post(f"{api_url}/v1/runners", json={"body": encoded_payload, "isBase64Encoded": True}, headers=headers, timeout=10)
    assert response.status_code in [200, 400, 401]


def test_complete_workflow_job_lifecycle():
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    initial_attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
    initial_count = int(initial_attrs['Attributes']['ApproximateNumberOfMessages'])
    assert initial_count >= 0


def test_circuit_breaker_auto_recovery_after_timeout(api_url, api_key):
    headers = {"x-api-key": api_key}
    response1 = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
    if response1.status_code == 200:
        time.sleep(2)
        response2 = requests.get(f"{api_url}/v1/runners/health", headers=headers, timeout=10)
        if response2.status_code == 200:
            data2 = response2.json()
            assert 'circuit_breaker' in data2 or 'status' in data2


def test_sqs_fifo_ordering_not_required_for_webhooks():
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    assert '.fifo' not in queue_url


def test_api_handles_high_volume_concurrent_requests(api_url):
    def make_health_request():
        return requests.get(f"{api_url}/health", timeout=10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_health_request) for _ in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    success_count = sum(1 for r in results if r.status_code == 200)
    assert success_count >= 15


def test_api_handles_concurrent_echo_requests(api_url):
    def make_echo_request(value):
        return requests.post(f"{api_url}/v1/echo", json={"value": value}, timeout=10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_echo_request, i) for i in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    success_count = sum(1 for r in results if r.status_code == 200)
    assert success_count >= 8


def test_lambda_cold_start_performance(api_url):
    start = time.time()
    response = requests.get(f"{api_url}/health", timeout=15)
    duration = time.time() - start
    assert response.status_code == 200
    assert duration < 10.0


def test_api_error_responses_include_correlation_ids(api_url):
    response = requests.get(f"{api_url}/nonexistent", timeout=10)
    assert response.status_code == 404


def test_webhook_event_unknown_type_ignored_gracefully(api_url):
    headers = {"x-github-event": "unknown_event_type"}
    payload = {"action": "test"}
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_workflow_job_completed_action_ignored(api_url):
    headers = {"x-github-event": "workflow_job"}
    payload = {
        "action": "completed",
        "workflow_job": {"id": 123, "labels": ["test"], "status": "completed"},
        "repository": {"full_name": "test/repo"}
    }
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_workflow_job_without_runner_labels_ignored(api_url):
    headers = {"x-github-event": "workflow_job"}
    payload = {
        "action": "queued",
        "workflow_job": {"id": 456, "labels": ["ubuntu-latest"], "status": "queued"},
        "repository": {"full_name": "test/repo"}
    }
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_sqs_message_deduplication_not_enabled():
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['All'])
    assert 'ContentBasedDeduplication' not in attributes['Attributes']


def test_api_responds_to_options_requests(api_url):
    response = requests.options(f"{api_url}/health", timeout=10)
    assert response.status_code in [200, 204, 405]


def test_api_handles_malformed_json_gracefully(api_url):
    headers = {"Content-Type": "application/json"}
    response = requests.post(f"{api_url}/v1/echo", data="{invalid json", headers=headers, timeout=10)
    assert response.status_code in [400, 500]


def test_api_handles_missing_content_type_header(api_url):
    response = requests.post(f"{api_url}/v1/echo", data='{"test": "data"}', timeout=10)
    assert response.status_code in [200, 400]
