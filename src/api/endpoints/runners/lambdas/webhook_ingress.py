"""Webhook ingress handlers for API Gateway → SQS direct integration.

This module handles webhooks that come through the SQS ingress queue,
bypassing Lambda in the API Gateway hot path to prevent throttling issues.
"""
import json
import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)


def get_message_attribute(record: Dict[str, Any], attr_name: str) -> str | None:
    """Extract message attribute from SQS record."""
    attrs = record.get('messageAttributes', {})
    attr = attrs.get(attr_name, {})
    return attr.get('stringValue')


def is_webhook_ingress_queue(event_source_arn: str) -> bool:
    """Check if the SQS event source is the webhook ingress queue."""
    return 'Ingress' in event_source_arn


def is_cleanup_queue(event_source_arn: str) -> bool:
    """Check if the SQS event source is the cleanup queue."""
    return 'Cleanup' in event_source_arn


class IngressHandler:
    """Handler for webhook ingress queue messages.

    Accepts a dependencies dict with keys: get_webhook_secret, verify_signature,
    publish_metric, check_idempotency, get_runner_type, enqueue_job,
    enqueue_cleanup, enqueue_ignored.
    """

    def __init__(self, deps: Dict[str, Any]):
        """Initialize with dependency functions dict from webhook_router."""
        self._deps = deps

    def get_deps(self) -> Dict[str, Any]:
        """Return dependencies dict for testing/inspection."""
        return self._deps

    def _verify_signature(self, body_str: str, signature: str | None,
                          delivery_id: str | None) -> Dict[str, Any] | None:
        """Verify webhook signature. Returns error dict or None."""
        if not signature:
            logger.warning("No signature header in webhook ingress message")
            return None
        try:
            webhook_secret = self._deps['get_webhook_secret']()
            if not self._deps['verify_signature'](body_str, signature, webhook_secret):
                logger.error("Invalid signature for delivery %s", delivery_id)
                self._deps['publish_metric']('InvalidSignature', 1.0, 'Count')
                return {'success': True, 'skipped': True,
                        'reason': 'invalid_signature'}
        except RuntimeError as e:
            logger.error("Cannot verify signature: %s", e)
            return {'success': False, 'error': str(e)}
        return None

    def _route_workflow_job(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route workflow_job event to appropriate queue."""
        action = payload.get('action')
        if action != 'queued':
            logger.info("Ignoring workflow_job action '%s'", action)
            self._deps['enqueue_ignored'](payload, f'workflow_job action {action} ignored')
            return {'success': True, 'routed': 'ignored_events'}

        job = payload.get('workflow_job', {})
        job_labels = job.get('labels', [])
        runner_type, _ = self._deps['get_runner_type'](job_labels)

        if not runner_type:
            logger.info("Job labels %s don't match EC2/Fargate", job_labels)
            self._deps['enqueue_ignored'](payload, 'no matching runner type')
            return {'success': True, 'routed': 'ignored_events'}

        job_data = {
            'job_id': job.get('id'),
            'job_labels': job_labels,
            'github_repo': payload.get('repository', {}).get('full_name'),
            'run_id': job.get('run_id'),
            'runner_type': runner_type
        }
        result = self._deps['enqueue_job'](job_data)
        return {'success': result['success'], 'routed': 'job_queue'}

    def _route_workflow_run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route workflow_run event to cleanup queue."""
        action = payload.get('action')
        if action != 'completed':
            logger.info("Ignoring workflow_run action '%s'", action)
            self._deps['enqueue_ignored'](payload, f'workflow_run action {action} ignored')
            return {'success': True, 'routed': 'ignored_events'}

        workflow_run = payload.get('workflow_run', {})
        cleanup_data = {
            'type': 'cleanup',
            'run_id': str(workflow_run.get('id')),
            'workflow_name': workflow_run.get('name'),
            'conclusion': workflow_run.get('conclusion')
        }
        result = self._deps['enqueue_cleanup'](cleanup_data)
        return {'success': result['success'], 'routed': 'cleanup_queue'}

    def _route_event(self, github_event: str | None,
                     payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route webhook ingress event based on event type."""
        if github_event == 'workflow_job':
            return self._route_workflow_job(payload)
        if github_event == 'workflow_run':
            return self._route_workflow_run(payload)
        if github_event == 'ping':
            logger.info("Received ping event via ingress queue")
            return {'success': True, 'routed': 'ping_acknowledged'}
        logger.info("Ignoring event type: %s", github_event)
        self._deps['enqueue_ignored'](payload, f'event type {github_event} ignored')
        return {'success': True, 'routed': 'ignored_events'}

    def handle(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Process webhook from ingress queue."""
        start_time = time.time()
        github_event = get_message_attribute(record, 'x-github-event')
        signature = get_message_attribute(record, 'x-hub-signature-256')
        delivery_id = get_message_attribute(record, 'x-github-delivery')
        body_str = record.get('body', '')

        logger.info("Processing webhook ingress: event=%s, delivery=%s",
                    github_event, delivery_id)

        sig_error = self._verify_signature(body_str, signature, delivery_id)
        if sig_error:
            return sig_error

        if delivery_id and self._deps['check_idempotency'](delivery_id):
            logger.info("Duplicate webhook delivery %s detected", delivery_id)
            return {'success': True, 'skipped': True, 'reason': 'duplicate'}

        try:
            payload = json.loads(body_str)
        except (ValueError, KeyError) as e:
            logger.error("Failed to parse webhook body: %s", e)
            return {'success': True, 'skipped': True, 'reason': 'invalid_json'}

        elapsed_ms = (time.time() - start_time) * 1000
        self._deps['publish_metric']('WebhookIngressProcessingTime', elapsed_ms,
                                     'Milliseconds')
        return self._route_event(github_event, payload)
