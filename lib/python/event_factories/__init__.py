"""Factory functions for creating test events."""
import json
import time
from typing import Any, Callable, Dict, List, Optional


def create_workflow_job_event(
    action: str = 'queued',
    job_id: int = 123,
    labels: Optional[List[str]] = None,
    repo: str = 'test/repo',
    run_id: int = 456
) -> Dict[str, Any]:
    """Create a workflow_job webhook event.

    Args:
        action: The action type ('queued', 'in_progress', 'completed').
        job_id: The workflow job ID.
        labels: List of runner labels. Defaults to ['self-hosted', 'linux'].
        repo: Repository full name (owner/repo).
        run_id: The workflow run ID.

    Returns:
        Dict representing a GitHub workflow_job webhook event.
    """
    if labels is None:
        labels = ['self-hosted', 'linux']
    return {
        'path': '/v1/runners',
        'httpMethod': 'POST',
        'headers': {
            'X-GitHub-Event': 'workflow_job',
            'X-Hub-Signature-256': 'sha256=test'
        },
        'body': json.dumps({
            'action': action,
            'workflow_job': {
                'id': job_id,
                'run_id': run_id,
                'labels': labels,
                'status': 'queued' if action == 'queued' else 'completed'
            },
            'repository': {
                'full_name': repo
            }
        })
    }


def workflow_job_event_factory() -> Callable[..., Dict[str, Any]]:
    """Return a factory function for creating workflow_job events.

    Returns:
        Factory function that creates workflow_job webhook events.
    """
    return create_workflow_job_event


def create_sqs_event(
    records: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Create an SQS trigger event.

    Args:
        records: List of SQS record dicts. Defaults to a single test record.

    Returns:
        Dict representing an SQS Lambda trigger event.
    """
    if records is None:
        records = [{
            'messageId': 'test-message-id',
            'body': json.dumps({'job_id': 123, 'action': 'test'}),
            'attributes': {},
            'messageAttributes': {}
        }]
    return {'Records': records}


def sqs_event_factory() -> Callable[..., Dict[str, Any]]:
    """Return a factory function for creating SQS events.

    Returns:
        Factory function that creates SQS Lambda trigger events.
    """
    return create_sqs_event


def create_dlq_message(
    body: Optional[Dict[str, Any]] = None,
    receipt_handle: str = 'test-receipt',
    attributes: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create a DLQ message.

    Args:
        body: Message body dict. Defaults to {'job_id': 123, 'action': 'test'}.
        receipt_handle: SQS receipt handle.
        attributes: Message attributes. Defaults to {'ApproximateReceiveCount': '1'}.

    Returns:
        Dict representing a DLQ message.
    """
    if body is None:
        body = {'job_id': 123, 'action': 'test'}
    if attributes is None:
        attributes = {'ApproximateReceiveCount': '1'}
    return {
        'MessageId': 'test-message-id',
        'ReceiptHandle': receipt_handle,
        'Body': json.dumps(body),
        'Attributes': attributes,
        'MessageAttributes': {}
    }


def dlq_message_factory() -> Callable[..., Dict[str, Any]]:
    """Return a factory function for creating DLQ messages.

    Returns:
        Factory function that creates DLQ messages.
    """
    return create_dlq_message


def create_circuit_breaker_closed_state() -> Dict[str, Any]:
    """Create a closed circuit breaker state.

    Returns:
        Dict representing a closed circuit breaker state.
    """
    return {
        'state': 'closed',
        'failure_count': 0,
        'last_failure_time': None
    }


def create_circuit_breaker_open_state() -> Dict[str, Any]:
    """Create an open circuit breaker state.

    Returns:
        Dict representing an open circuit breaker state with current timestamp.
    """
    return {
        'state': 'open',
        'failure_count': 5,
        'last_failure_time': time.time()
    }


def create_ecs_runner_post_event(
    job_id: int = 123,
    job_labels: Optional[List[str]] = None,
    github_repo: str = 'test/repo'
) -> Dict[str, Any]:
    """Create an ECS runner POST event.

    Args:
        job_id: The workflow job ID.
        job_labels: List of runner labels. Defaults to ['fargate', 'self-hosted'].
        github_repo: Repository full name (owner/repo).

    Returns:
        Dict representing an ECS runner POST API event.
    """
    if job_labels is None:
        job_labels = ['fargate', 'self-hosted']
    return {
        'path': '/v1/runners/ecs',
        'httpMethod': 'POST',
        'body': json.dumps({
            'job_id': job_id,
            'job_labels': job_labels,
            'github_repo': github_repo
        })
    }
