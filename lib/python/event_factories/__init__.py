import json
from typing import Any, Callable, Dict, List, Optional


def create_sqs_event(
    records: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    if records is None:
        records = [{
            'messageId': 'test-message-id',
            'body': json.dumps({'job_id': 123, 'action': 'test'}),
            'attributes': {},
            'messageAttributes': {}
        }]
    return {'Records': records}


def sqs_event_factory() -> Callable[..., Dict[str, Any]]:
    return create_sqs_event


def create_dlq_message(
    body: Optional[Dict[str, Any]] = None,
    receipt_handle: str = 'test-receipt',
    attributes: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
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
    return create_dlq_message
