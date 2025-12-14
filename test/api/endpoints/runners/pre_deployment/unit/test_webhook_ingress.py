"""Unit tests for webhook_ingress module."""
import json


def test_is_webhook_ingress_queue_returns_true_for_ingress(webhook_ingress):
    """Test is_webhook_ingress_queue returns true for ingress queue ARN."""
    arn = "arn:aws:sqs:us-east-1:123456789:TestHandlerIngress"
    assert webhook_ingress.is_webhook_ingress_queue(arn) is True


def test_is_webhook_ingress_queue_returns_false_for_job_queue(webhook_ingress):
    """Test is_webhook_ingress_queue returns false for job queue ARN."""
    arn = "arn:aws:sqs:us-east-1:123456789:TestHandlerJobs"
    assert webhook_ingress.is_webhook_ingress_queue(arn) is False


def test_get_message_attribute_extracts_value(webhook_ingress):
    """Test get_message_attribute extracts string value from SQS record."""
    record = {
        'messageAttributes': {
            'x-github-event': {'stringValue': 'workflow_job'}
        }
    }
    result = webhook_ingress.get_message_attribute(record, 'x-github-event')
    assert result == 'workflow_job'


def test_get_message_attribute_returns_none_for_missing(webhook_ingress):
    """Test get_message_attribute returns None for missing attribute."""
    record = {'messageAttributes': {}}
    result = webhook_ingress.get_message_attribute(record, 'x-github-event')
    assert result is None


def test_ingress_handler_invalid_signature_returns_success(webhook_ingress):
    """Test IngressHandler with invalid signature returns success."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: False,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: ('ec2', None),
        'enqueue_job': lambda x: {'success': True},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    record = {
        'body': '{"action": "queued"}',
        'messageAttributes': {
            'x-hub-signature-256': {'stringValue': 'sha256=invalid'},
            'x-github-event': {'stringValue': 'workflow_job'},
            'x-github-delivery': {'stringValue': 'test-delivery-id'}
        }
    }
    result = handler.handle(record)
    assert result['success'] is True


def test_ingress_handler_invalid_signature_sets_skipped(webhook_ingress):
    """Test IngressHandler with invalid signature sets skipped reason."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: False,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: ('ec2', None),
        'enqueue_job': lambda x: {'success': True},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    record = {
        'body': '{"action": "queued"}',
        'messageAttributes': {
            'x-hub-signature-256': {'stringValue': 'sha256=invalid'},
            'x-github-event': {'stringValue': 'workflow_job'},
            'x-github-delivery': {'stringValue': 'test-delivery-id'}
        }
    }
    result = handler.handle(record)
    assert result.get('reason') == 'invalid_signature'


def test_ingress_handler_workflow_job_queued_returns_success(webhook_ingress):
    """Test IngressHandler workflow_job queued returns success."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: True,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: ('ec2', None),
        'enqueue_job': lambda x: {'success': True, 'message_id': 'msg-123'},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    payload = json.dumps({
        'action': 'queued',
        'workflow_job': {'id': 123, 'labels': ['self-hosted']},
        'repository': {'full_name': 'org/repo'}
    })
    record = {
        'body': payload,
        'messageAttributes': {
            'x-hub-signature-256': {'stringValue': 'sha256=valid'},
            'x-github-event': {'stringValue': 'workflow_job'},
            'x-github-delivery': {'stringValue': 'test-delivery-id'}
        }
    }
    result = handler.handle(record)
    assert result['success'] is True


def test_ingress_handler_workflow_job_queued_routes_to_job_queue(webhook_ingress):
    """Test IngressHandler routes workflow_job queued to job queue."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: True,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: ('ec2', None),
        'enqueue_job': lambda x: {'success': True, 'message_id': 'msg-123'},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    payload = json.dumps({
        'action': 'queued',
        'workflow_job': {'id': 123, 'labels': ['self-hosted']},
        'repository': {'full_name': 'org/repo'}
    })
    record = {
        'body': payload,
        'messageAttributes': {
            'x-hub-signature-256': {'stringValue': 'sha256=valid'},
            'x-github-event': {'stringValue': 'workflow_job'},
            'x-github-delivery': {'stringValue': 'test-delivery-id'}
        }
    }
    result = handler.handle(record)
    assert result.get('routed') == 'job_queue'


def test_ingress_handler_workflow_run_completed_routes_to_cleanup(webhook_ingress):
    """Test IngressHandler routes workflow_run completed to cleanup queue."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: True,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: ('ec2', None),
        'enqueue_job': lambda x: {'success': True},
        'enqueue_cleanup': lambda x: {'success': True, 'message_id': 'msg-456'},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    payload = json.dumps({
        'action': 'completed',
        'workflow_run': {'id': 789, 'name': 'wf', 'conclusion': 'success'}
    })
    record = {
        'body': payload,
        'messageAttributes': {
            'x-hub-signature-256': {'stringValue': 'sha256=valid'},
            'x-github-event': {'stringValue': 'workflow_run'},
            'x-github-delivery': {'stringValue': 'test-delivery-id'}
        }
    }
    result = handler.handle(record)
    assert result.get('routed') == 'cleanup_queue'


def test_ingress_handler_ping_acknowledged(webhook_ingress):
    """Test IngressHandler acknowledges ping events."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: True,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: (None, None),
        'enqueue_job': lambda x: {'success': True},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    payload = '{"zen": "Design for failure", "hook_id": 123}'
    record = {
        'body': payload,
        'messageAttributes': {
            'x-hub-signature-256': {'stringValue': 'sha256=valid'},
            'x-github-event': {'stringValue': 'ping'},
            'x-github-delivery': {'stringValue': 'test-delivery-id'}
        }
    }
    result = handler.handle(record)
    assert result.get('routed') == 'ping_acknowledged'


def test_ingress_handler_unknown_event_routes_to_ignored(webhook_ingress):
    """Test IngressHandler routes unknown events to ignored queue."""
    ignored_called = []
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: True,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: (None, None),
        'enqueue_job': lambda x: {'success': True},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: ignored_called.append((x, y))
    }
    handler = webhook_ingress.IngressHandler(deps)
    payload = '{"action": "created", "issue": {"id": 123}}'
    record = {
        'body': payload,
        'messageAttributes': {
            'x-hub-signature-256': {'stringValue': 'sha256=valid'},
            'x-github-event': {'stringValue': 'issues'},
            'x-github-delivery': {'stringValue': 'test-delivery-id'}
        }
    }
    result = handler.handle(record)
    assert result.get('routed') == 'ignored_events'


def test_ingress_handler_wrapped_format_parses_successfully(webhook_ingress):
    """Test IngressHandler parses wrapped format from API Gateway."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: True,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: ('ec2', None),
        'enqueue_job': lambda x: {'success': True, 'message_id': 'msg-123'},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    inner_payload = json.dumps({
        'action': 'queued',
        'workflow_job': {'id': 123, 'labels': ['self-hosted']},
        'repository': {'full_name': 'org/repo'}
    })
    wrapped = json.dumps({
        'headers': {
            'x-github-event': 'workflow_job',
            'x-hub-signature-256': 'sha256=valid',
            'x-github-delivery': 'test-delivery-id'
        },
        'body': inner_payload
    })
    record = {'body': wrapped, 'messageAttributes': {}}
    result = handler.handle(record)
    assert result['success'] is True


def test_ingress_handler_wrapped_format_routes_to_job_queue(webhook_ingress):
    """Test IngressHandler routes wrapped format workflow_job to job queue."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: True,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: ('ec2', None),
        'enqueue_job': lambda x: {'success': True, 'message_id': 'msg-123'},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    inner_payload = json.dumps({
        'action': 'queued',
        'workflow_job': {'id': 123, 'labels': ['self-hosted']},
        'repository': {'full_name': 'org/repo'}
    })
    wrapped = json.dumps({
        'headers': {
            'x-github-event': 'workflow_job',
            'x-hub-signature-256': 'sha256=valid',
            'x-github-delivery': 'test-delivery-id'
        },
        'body': inner_payload
    })
    record = {'body': wrapped, 'messageAttributes': {}}
    result = handler.handle(record)
    assert result.get('routed') == 'job_queue'


def test_ingress_handler_wrapped_format_missing_body_returns_success(webhook_ingress):
    """Test IngressHandler returns success for wrapped format with no body."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: True,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: (None, None),
        'enqueue_job': lambda x: {'success': True},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    wrapped = json.dumps({
        'headers': {
            'x-github-event': 'workflow_job',
            'x-hub-signature-256': 'sha256=valid',
            'x-github-delivery': 'test-delivery-id'
        }
    })
    record = {'body': wrapped, 'messageAttributes': {}}
    result = handler.handle(record)
    assert result['success'] is True


def test_ingress_handler_wrapped_format_missing_body_sets_skipped(webhook_ingress):
    """Test IngressHandler sets skipped for wrapped format with no body."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: True,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: (None, None),
        'enqueue_job': lambda x: {'success': True},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    wrapped = json.dumps({
        'headers': {
            'x-github-event': 'workflow_job',
            'x-hub-signature-256': 'sha256=valid',
            'x-github-delivery': 'test-delivery-id'
        }
    })
    record = {'body': wrapped, 'messageAttributes': {}}
    result = handler.handle(record)
    assert result.get('skipped') is True


def test_ingress_handler_wrapped_format_missing_body_reason_invalid_json(webhook_ingress):
    """Test IngressHandler sets reason=invalid_json for wrapped format with no body."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: True,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: (None, None),
        'enqueue_job': lambda x: {'success': True},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    wrapped = json.dumps({
        'headers': {
            'x-github-event': 'workflow_job',
            'x-hub-signature-256': 'sha256=valid',
            'x-github-delivery': 'test-delivery-id'
        }
    })
    record = {'body': wrapped, 'messageAttributes': {}}
    result = handler.handle(record)
    assert result.get('reason') == 'invalid_json'


def test_ingress_handler_wrapped_format_empty_headers_returns_success(webhook_ingress):
    """Test IngressHandler returns success for empty header values."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: True,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: (None, None),
        'enqueue_job': lambda x: {'success': True},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    wrapped = json.dumps({
        'headers': {
            'x-github-event': '',
            'x-hub-signature-256': '',
            'x-github-delivery': ''
        },
        'body': '{}'
    })
    record = {'body': wrapped, 'messageAttributes': {}}
    result = handler.handle(record)
    assert result['success'] is True


def test_ingress_handler_wrapped_format_empty_headers_routes_to_ignored(webhook_ingress):
    """Test IngressHandler routes empty header values to ignored events."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: True,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: (None, None),
        'enqueue_job': lambda x: {'success': True},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    wrapped = json.dumps({
        'headers': {
            'x-github-event': '',
            'x-hub-signature-256': '',
            'x-github-delivery': ''
        },
        'body': '{}'
    })
    record = {'body': wrapped, 'messageAttributes': {}}
    result = handler.handle(record)
    assert result.get('routed') == 'ignored_events'


def test_ingress_handler_legacy_format_returns_success(webhook_ingress):
    """Test IngressHandler returns success for legacy format."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: True,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: ('ec2', None),
        'enqueue_job': lambda x: {'success': True, 'message_id': 'msg-123'},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    payload = json.dumps({
        'action': 'queued',
        'workflow_job': {'id': 123, 'labels': ['self-hosted']},
        'repository': {'full_name': 'org/repo'}
    })
    record = {
        'body': payload,
        'messageAttributes': {
            'x-hub-signature-256': {'stringValue': 'sha256=valid'},
            'x-github-event': {'stringValue': 'workflow_job'},
            'x-github-delivery': {'stringValue': 'test-delivery-id'}
        }
    }
    result = handler.handle(record)
    assert result['success'] is True


def test_ingress_handler_legacy_format_routes_to_job_queue(webhook_ingress):
    """Test IngressHandler routes legacy format to job queue."""
    deps = {
        'get_webhook_secret': lambda: 'test-secret',
        'verify_signature': lambda body, sig, secret: True,
        'publish_metric': lambda *args: None,
        'check_idempotency': lambda x: False,
        'get_runner_type': lambda x: ('ec2', None),
        'enqueue_job': lambda x: {'success': True, 'message_id': 'msg-123'},
        'enqueue_cleanup': lambda x: {'success': True},
        'enqueue_ignored': lambda x, y: None
    }
    handler = webhook_ingress.IngressHandler(deps)
    payload = json.dumps({
        'action': 'queued',
        'workflow_job': {'id': 123, 'labels': ['self-hosted']},
        'repository': {'full_name': 'org/repo'}
    })
    record = {
        'body': payload,
        'messageAttributes': {
            'x-hub-signature-256': {'stringValue': 'sha256=valid'},
            'x-github-event': {'stringValue': 'workflow_job'},
            'x-github-delivery': {'stringValue': 'test-delivery-id'}
        }
    }
    result = handler.handle(record)
    assert result.get('routed') == 'job_queue'
