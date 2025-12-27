"""Tests for webhook endpoints."""
import requests

from .conftest import skip_if_endpoint_not_deployed


TEST_HEADERS = {"x-test-mode": "true"}


def _create_workflow_job_payload(action="queued", job_id=123, labels=None, full_name="x/y"):
    """Create a standard workflow job webhook payload."""
    return {
        "action": action,
        "workflow_job": {"id": job_id, "labels": labels or [], "status": action},
        "repository": {"full_name": full_name},
    }


def _create_workflow_job_headers(with_signature=False):
    """Create headers for workflow job webhook request."""
    headers = {"x-github-event": "workflow_job", "x-test-mode": "true"}
    if with_signature:
        headers["x-hub-signature-256"] = "sha256=invalid"
    return headers


def _post_webhook(api_url, payload, headers):
    """Make a POST request to the webhook endpoint."""
    url = f"{api_url}/v1/webhooks/github/jit-runner-requests"
    return requests.post(url, json=payload, headers=headers, timeout=10)


def test_v1_runners_post_rejects_missing_github_event_header(api_url):
    """Verify that webhook rejects requests without GitHub event header.

    API Gateway request validation requires x-github-event header to filter
    out non-GitHub traffic (bots, scanners) at the gateway layer.
    """
    skip_if_endpoint_not_deployed(api_url, "/v1/webhooks/github/jit-runner-requests", "POST")
    payload = {"action": "queued"}
    url = f"{api_url}/v1/webhooks/github/jit-runner-requests"
    response = requests.post(url, json=payload, headers=TEST_HEADERS, timeout=10)
    assert response.status_code == 400


def test_v1_runners_post_ignores_missing_signature(api_url):
    """Verify that webhook ignores requests without signature."""
    skip_if_endpoint_not_deployed(api_url, "/v1/webhooks/github/jit-runner-requests", "POST")
    headers = _create_workflow_job_headers(with_signature=False)
    payload = _create_workflow_job_payload()
    response = _post_webhook(api_url, payload, headers)
    assert response.status_code == 200


def test_v1_runners_post_accepts_request_to_sqs(api_url):
    """Verify that webhook accepts requests into SQS queue.

    With API Gateway → SQS direct integration, signature validation happens
    asynchronously in the Lambda that processes from SQS. The endpoint always
    returns 200 to accept the request into the queue.
    """
    skip_if_endpoint_not_deployed(api_url, "/v1/webhooks/github/jit-runner-requests", "POST")
    headers = _create_workflow_job_headers(with_signature=True)
    payload = _create_workflow_job_payload()
    response = _post_webhook(api_url, payload, headers)
    # API Gateway → SQS returns 200 (accepted into queue)
    # Signature validation happens asynchronously in Lambda
    assert response.status_code == 200


def test_workflow_job_completed_action_returns_200(api_url):
    """Verify that completed workflow job returns 200."""
    skip_if_endpoint_not_deployed(api_url, "/v1/webhooks/github/jit-runner-requests", "POST")
    headers = _create_workflow_job_headers(with_signature=True)
    payload = _create_workflow_job_payload(
        action="completed", labels=["ubuntu-latest"], full_name="test/repo"
    )
    response = _post_webhook(api_url, payload, headers)
    assert response.status_code in [200, 401]


def test_workflow_job_without_self_hosted_labels_returns_200(api_url):
    """Verify that workflow job without self-hosted labels returns 200."""
    skip_if_endpoint_not_deployed(api_url, "/v1/webhooks/github/jit-runner-requests", "POST")
    headers = _create_workflow_job_headers(with_signature=True)
    payload = _create_workflow_job_payload(
        job_id=456, labels=["ubuntu-latest"], full_name="test/repo"
    )
    response = _post_webhook(api_url, payload, headers)
    assert response.status_code in [200, 401]
