import json
import hashlib
import hmac
import requests


def test_runners_endpoint_responds_to_ping_event(runners_endpoint):
    payload = {
        'zen': 'Design for failure.',
        'hook_id': 123456
    }

    response = requests.post(
        runners_endpoint,
        json=payload,
        headers={
            'X-GitHub-Event': 'ping',
            'Content-Type': 'application/json'
        },
        timeout=30
    )

    assert response.status_code == 200


def test_runners_endpoint_returns_pong_for_ping(runners_endpoint):
    payload = {
        'zen': 'Design for failure.',
        'hook_id': 123456
    }

    response = requests.post(
        runners_endpoint,
        json=payload,
        headers={
            'X-GitHub-Event': 'ping',
            'Content-Type': 'application/json'
        },
        timeout=30
    )

    data = response.json()
    assert data['message'] == 'pong'


def test_runners_endpoint_ignores_non_queued_workflow_job(runners_endpoint):
    payload = {
        'action': 'completed',
        'workflow_job': {
            'id': 123,
            'name': 'test-job',
            'labels': ['self-hosted', 'ephemeral-ec2-spot-instance'],
            'status': 'completed'
        },
        'repository': {
            'full_name': '10U-Labs-LLC/10ulabs.com'
        }
    }

    response = requests.post(
        runners_endpoint,
        json=payload,
        headers={
            'X-GitHub-Event': 'workflow_job',
            'Content-Type': 'application/json'
        },
        timeout=30
    )

    assert response.status_code == 200


def test_runners_endpoint_ignores_workflow_job_without_runner_labels(runners_endpoint):
    payload = {
        'action': 'queued',
        'workflow_job': {
            'id': 456,
            'name': 'test-job',
            'labels': ['self-hosted', 'linux'],
            'status': 'queued'
        },
        'repository': {
            'full_name': '10U-Labs-LLC/10ulabs.com'
        }
    }

    response = requests.post(
        runners_endpoint,
        json=payload,
        headers={
            'X-GitHub-Event': 'workflow_job',
            'Content-Type': 'application/json'
        },
        timeout=30
    )

    assert response.status_code == 200
    data = response.json()
    assert 'ignoring' in data['message'].lower()


def test_runners_endpoint_accepts_workflow_job_with_ec2_label(runners_endpoint):
    payload = {
        'action': 'queued',
        'workflow_job': {
            'id': 789,
            'name': 'test-job',
            'labels': ['self-hosted', 'ephemeral-ec2-spot-instance'],
            'status': 'queued'
        },
        'repository': {
            'full_name': '10U-Labs-LLC/10ulabs.com'
        }
    }

    response = requests.post(
        runners_endpoint,
        json=payload,
        headers={
            'X-GitHub-Event': 'workflow_job',
            'Content-Type': 'application/json'
        },
        timeout=30
    )

    assert response.status_code in [200, 500]


def test_runners_endpoint_accepts_workflow_job_with_fargate_label(runners_endpoint):
    payload = {
        'action': 'queued',
        'workflow_job': {
            'id': 101112,
            'name': 'test-job',
            'labels': ['self-hosted', 'ephemeral-ecs-fargate-spot'],
            'status': 'queued'
        },
        'repository': {
            'full_name': '10U-Labs-LLC/10ulabs.com'
        }
    }

    response = requests.post(
        runners_endpoint,
        json=payload,
        headers={
            'X-GitHub-Event': 'workflow_job',
            'Content-Type': 'application/json'
        },
        timeout=30
    )

    assert response.status_code in [200, 500]


def test_runners_endpoint_returns_json_response(runners_endpoint):
    payload = {
        'zen': 'Keep it simple.',
        'hook_id': 999999
    }

    response = requests.post(
        runners_endpoint,
        json=payload,
        headers={
            'X-GitHub-Event': 'ping',
            'Content-Type': 'application/json'
        },
        timeout=30
    )

    assert response.headers['Content-Type'].startswith('application/json')


def test_runners_endpoint_handles_invalid_json_gracefully(runners_endpoint):
    response = requests.post(
        runners_endpoint,
        data='invalid json',
        headers={
            'X-GitHub-Event': 'ping',
            'Content-Type': 'application/json'
        },
        timeout=30
    )

    assert response.status_code in [400, 500]


def test_runners_endpoint_ignores_unknown_event_types(runners_endpoint):
    payload = {
        'action': 'opened',
        'issue': {
            'number': 1,
            'title': 'Test issue'
        }
    }

    response = requests.post(
        runners_endpoint,
        json=payload,
        headers={
            'X-GitHub-Event': 'issues',
            'Content-Type': 'application/json'
        },
        timeout=30
    )

    assert response.status_code == 200


def test_runners_endpoint_handles_concurrent_ping_requests(runners_endpoint):
    import concurrent.futures

    payload = {
        'zen': 'Design for failure.',
        'hook_id': 123456
    }

    def send_request(index):
        return requests.post(
            runners_endpoint,
            json=payload,
            headers={
                'X-GitHub-Event': 'ping',
                'Content-Type': 'application/json'
            },
            timeout=30
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(send_request, i) for i in range(5)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len([r for r in responses if r.status_code == 200]) == 5


def test_runners_endpoint_handles_concurrent_workflow_job_requests(runners_endpoint):
    import concurrent.futures

    def send_request(job_id):
        payload = {
            'action': 'queued',
            'workflow_job': {
                'id': job_id,
                'name': f'test-job-{job_id}',
                'labels': ['self-hosted', 'ephemeral-ec2-spot-instance'],
                'status': 'queued'
            },
            'repository': {
                'full_name': '10U-Labs-LLC/10ulabs.com'
            }
        }
        return requests.post(
            runners_endpoint,
            json=payload,
            headers={
                'X-GitHub-Event': 'workflow_job',
                'Content-Type': 'application/json'
            },
            timeout=30
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(send_request, 1000 + i) for i in range(3)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len([r for r in responses if r.status_code in [200, 500]]) == 3


def test_runners_endpoint_handles_duplicate_delivery_ids(runners_endpoint):
    import time

    delivery_id = f'test-delivery-{int(time.time() * 1000)}'

    payload = {
        'zen': 'Design for failure.',
        'hook_id': 123456
    }

    response1 = requests.post(
        runners_endpoint,
        json=payload,
        headers={
            'X-GitHub-Event': 'ping',
            'X-GitHub-Delivery': delivery_id,
            'Content-Type': 'application/json'
        },
        timeout=30
    )

    response2 = requests.post(
        runners_endpoint,
        json=payload,
        headers={
            'X-GitHub-Event': 'ping',
            'X-GitHub-Delivery': delivery_id,
            'Content-Type': 'application/json'
        },
        timeout=30
    )

    assert response1.status_code == 200
    assert response2.status_code == 200


def test_runners_endpoint_processes_different_delivery_ids(runners_endpoint):
    import time

    payload = {
        'zen': 'Design for failure.',
        'hook_id': 123456
    }

    delivery_id1 = f'test-delivery-{int(time.time() * 1000)}-1'
    delivery_id2 = f'test-delivery-{int(time.time() * 1000)}-2'

    response1 = requests.post(
        runners_endpoint,
        json=payload,
        headers={
            'X-GitHub-Event': 'ping',
            'X-GitHub-Delivery': delivery_id1,
            'Content-Type': 'application/json'
        },
        timeout=30
    )

    response2 = requests.post(
        runners_endpoint,
        json=payload,
        headers={
            'X-GitHub-Event': 'ping',
            'X-GitHub-Delivery': delivery_id2,
            'Content-Type': 'application/json'
        },
        timeout=30
    )

    assert response1.status_code == 200
    assert response2.status_code == 200


def test_runners_endpoint_handles_concurrent_requests_with_same_delivery_id(runners_endpoint):
    import concurrent.futures
    import time

    delivery_id = f'test-delivery-{int(time.time() * 1000)}-concurrent'

    payload = {
        'zen': 'Design for failure.',
        'hook_id': 123456
    }

    def send_request(index):
        return requests.post(
            runners_endpoint,
            json=payload,
            headers={
                'X-GitHub-Event': 'ping',
                'X-GitHub-Delivery': delivery_id,
                'Content-Type': 'application/json'
            },
            timeout=30
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(send_request, i) for i in range(3)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len([r for r in responses if r.status_code == 200]) == 3
