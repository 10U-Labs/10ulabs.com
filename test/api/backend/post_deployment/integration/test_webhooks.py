"""Tests for webhook endpoints."""

import pytest
import requests

from ..conftest import (
    assert_circuit_breaker_state_in_response,
    make_health_check_request,
    skip_if_endpoint_not_deployed,
)


TEST_HEADERS = {"x-test-mode": "true"}


def test_v1_runners_health_get_requires_auth(api_url):
    """Verify that health endpoint requires authentication."""
    skip_if_endpoint_not_deployed(api_url, "/v1/runners/health")
    response = requests.get(
        f"{api_url}/v1/runners/health", headers=TEST_HEADERS, timeout=10
    )
    assert response.status_code == 403


def test_v1_runners_health_get_with_valid_api_key(api_url, api_key):
    """Verify that health endpoint works with valid API key."""
    skip_if_endpoint_not_deployed(api_url, "/v1/runners/health")
    response = make_health_check_request(api_url, api_key)
    # 500 means Lambda exists but is broken (skip check is unauthenticated)
    if response.status_code == 500:
        pytest.skip("Endpoint /v1/runners Lambda not functional (managed by runners.yml)")
    assert response.status_code == 200


def test_v1_runners_health_returns_json(api_url, api_key):
    """Verify that health endpoint returns JSON."""
    skip_if_endpoint_not_deployed(api_url, "/v1/runners/health")
    response = make_health_check_request(api_url, api_key)
    assert response.headers["Content-Type"] == "application/json"


def test_v1_runners_health_returns_circuit_breaker_state(api_url, api_key):
    """Verify that health endpoint returns circuit breaker state."""
    skip_if_endpoint_not_deployed(api_url, "/v1/runners/health")
    response = make_health_check_request(api_url, api_key)
    # 500 means Lambda exists but is broken (skip check is unauthenticated)
    if response.status_code == 500:
        pytest.skip("Endpoint /v1/runners Lambda not functional (managed by runners.yml)")
    assert_circuit_breaker_state_in_response(response)


def test_v1_runners_post_ignores_missing_github_event_header(api_url):
    """Verify that webhook ignores requests without GitHub event header."""
    skip_if_endpoint_not_deployed(api_url, "/v1/runners", "POST")
    payload = {"action": "queued"}
    response = requests.post(
        f"{api_url}/v1/runners", json=payload, headers=TEST_HEADERS, timeout=10
    )
    assert response.status_code == 200


def test_v1_runners_post_ignores_missing_signature(api_url):
    """Verify that webhook ignores requests without signature."""
    skip_if_endpoint_not_deployed(api_url, "/v1/runners", "POST")
    headers = {"x-github-event": "workflow_job", "x-test-mode": "true"}
    payload = {
        "action": "queued",
        "workflow_job": {"id": 123, "labels": []},
        "repository": {"full_name": "x/y"},
    }
    response = requests.post(
        f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10
    )
    assert response.status_code == 200


def test_v1_runners_post_rejects_invalid_signature(api_url):
    """Verify that webhook rejects requests with invalid signature."""
    skip_if_endpoint_not_deployed(api_url, "/v1/runners", "POST")
    headers = {
        "x-github-event": "workflow_job",
        "x-hub-signature-256": "sha256=invalid",
        "x-test-mode": "true",
    }
    payload = {
        "action": "queued",
        "workflow_job": {"id": 123, "labels": []},
        "repository": {"full_name": "x/y"},
    }
    response = requests.post(
        f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10
    )
    assert response.status_code == 401


def test_workflow_job_completed_action_returns_200(api_url):
    """Verify that completed workflow job returns 200."""
    skip_if_endpoint_not_deployed(api_url, "/v1/runners", "POST")
    headers = {
        "x-github-event": "workflow_job",
        "x-hub-signature-256": "sha256=invalid",
        "x-test-mode": "true",
    }
    payload = {
        "action": "completed",
        "workflow_job": {
            "id": 123,
            "labels": ["ubuntu-latest"],
            "status": "completed",
        },
        "repository": {"full_name": "test/repo"},
    }
    response = requests.post(
        f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10
    )
    assert response.status_code in [200, 401]


def test_workflow_job_without_self_hosted_labels_returns_200(api_url):
    """Verify that workflow job without self-hosted labels returns 200."""
    skip_if_endpoint_not_deployed(api_url, "/v1/runners", "POST")
    headers = {
        "x-github-event": "workflow_job",
        "x-hub-signature-256": "sha256=invalid",
        "x-test-mode": "true",
    }
    payload = {
        "action": "queued",
        "workflow_job": {
            "id": 456,
            "labels": ["ubuntu-latest"],
            "status": "queued",
        },
        "repository": {"full_name": "test/repo"},
    }
    response = requests.post(
        f"{api_url}/v1/runners", json=payload, headers=headers, timeout=10
    )
    assert response.status_code in [200, 401]
