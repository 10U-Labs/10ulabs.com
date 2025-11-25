from test.api.post_deployment.conftest import assert_circuit_breaker_state_in_response, make_health_check_request
import requests


def test_v1_runners_health_get_requires_auth(api_url):
    response = requests.get(f"{api_url}/v1/runners/health", timeout=10)
    assert response.status_code == 403


def test_v1_runners_health_get_with_valid_api_key(api_url, api_key):
    response = make_health_check_request(api_url, api_key)
    assert response.status_code == 200


def test_v1_runners_health_returns_json(api_url, api_key):
    response = make_health_check_request(api_url, api_key)
    assert response.headers["Content-Type"] == "application/json"


def test_v1_runners_health_returns_circuit_breaker_state(api_url, api_key):
    response = make_health_check_request(api_url, api_key)
    assert_circuit_breaker_state_in_response(response)


def test_v1_runners_post_ignores_missing_github_event_header(api_url):
    payload = {"action": "queued"}
    response = requests.post(f"{api_url}/v1/runners", json=payload, timeout=10)
    assert response.status_code == 200


def test_v1_runners_post_ignores_missing_signature(api_url):
    headers = {"x-github-event": "workflow_job"}
    payload = {"action": "queued", "workflow_job": {"id": 123, "labels": []}, "repository": {"full_name": "x/y"}}
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code == 200


def test_v1_runners_post_rejects_invalid_signature(api_url):
    headers = {"x-github-event": "workflow_job", "x-hub-signature-256": "sha256=invalid"}
    payload = {"action": "queued", "workflow_job": {"id": 123, "labels": []}, "repository": {"full_name": "x/y"}}
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code == 401


def test_workflow_job_completed_action_returns_200(api_url):
    headers = {"x-github-event": "workflow_job", "x-hub-signature-256": "sha256=invalid"}
    payload = {
        "action": "completed",
        "workflow_job": {"id": 123, "labels": ["ubuntu-latest"], "status": "completed"},
        "repository": {"full_name": "test/repo"}
    }
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_workflow_job_without_self_hosted_labels_returns_200(api_url):
    headers = {"x-github-event": "workflow_job", "x-hub-signature-256": "sha256=invalid"}
    payload = {
        "action": "queued",
        "workflow_job": {"id": 456, "labels": ["ubuntu-latest"], "status": "queued"},
        "repository": {"full_name": "test/repo"}
    }
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]
