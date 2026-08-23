"""Factory functions for creating test events."""
import json
from typing import Any, Callable, Dict, List, Optional


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
