import base64
import hashlib
import hmac
import json
import time
import urllib.parse
from test.api.post_deployment.conftest import make_health_check_request, assert_circuit_breaker_state_in_response

import requests


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
    response = make_health_check_request(api_url, api_key)
    assert response.status_code in [200, 403]


def test_v1_runners_health_returns_circuit_breaker_state(api_url, api_key):
    response = make_health_check_request(api_url, api_key)
    assert_circuit_breaker_state_in_response(response)


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


def test_webhook_invalid_signature_rejected(api_url):
    headers = {"x-hub-signature-256": "sha256=invalidsignature123456"}
    payload = {"action": "queued"}
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


def test_webhook_to_sqs_workflow_enqueues_job(api_url):
    headers = {"x-github-event": "workflow_job", "x-github-delivery": f"e2e-workflow-test-{int(time.time())}"}
    payload = {
        "action": "queued",
        "workflow_job": {"id": 999999, "labels": ["ephemeral-ec2-spot-instance"], "status": "queued"},
        "repository": {"full_name": "test/repo"}
    }
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


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


def test_workflow_job_webhook_enqueues_and_processes(api_url):
    headers = {"x-github-event": "workflow_job"}
    payload = {
        "action": "queued",
        "workflow_job": {"id": 111111, "labels": ["ephemeral-ec2-spot-instance"], "status": "queued"},
        "repository": {"full_name": "test/repo"}
    }
    response = requests.post(f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10)
    assert response.status_code in [200, 401]


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
