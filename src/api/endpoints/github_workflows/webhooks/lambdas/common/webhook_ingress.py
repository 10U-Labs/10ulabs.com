"""Webhook ingress handling for SQS messages."""

import logging
import json
import time
from typing import Any, Protocol

logger = logging.getLogger(__name__)


def get_message_attribute(record: dict[str, Any], attr_name: str) -> str | None:
    """Extract a message attribute from an SQS record.

    Args:
        record: SQS record dictionary
        attr_name: Name of the attribute to extract

    Returns:
        Attribute value or None if not present
    """
    attrs = record.get("messageAttributes", {})
    attr = attrs.get(attr_name, {})
    return attr.get("stringValue")


def is_webhook_ingress_queue(event_source_arn: str) -> bool:
    """Check if the event source is a webhook ingress queue.

    Args:
        event_source_arn: ARN of the event source

    Returns:
        True if this is an ingress queue
    """
    return "Ingress" in event_source_arn


class IngressDeps(Protocol):
    """Protocol defining dependencies for IngressHandler."""

    async def get_webhook_secret(self) -> str:
        """Get the webhook secret for signature verification."""

    def verify_signature(self, body: str, signature: str, secret: str) -> bool:
        """Verify webhook signature."""

    def publish_metric(self, name: str, value: float, unit: str) -> None:
        """Publish a CloudWatch metric."""

    async def check_idempotency(self, delivery_id: str) -> bool:
        """Check if this delivery has already been processed."""

    def enqueue_ignored(self, payload: dict[str, Any], reason: str) -> None:
        """Enqueue an ignored event for archival."""


class IngressHandler:
    """Handle webhook ingress messages from SQS."""

    def __init__(self, deps: IngressDeps) -> None:
        """Initialize with dependencies.

        Args:
            deps: Object implementing IngressDeps protocol
        """
        self._deps = deps

    def get_deps(self) -> IngressDeps:
        """Get the dependencies object."""
        return self._deps

    async def _verify_signature(
        self, body_str: str, signature: str | None, delivery_id: str | None
    ) -> dict[str, Any] | None:
        """Verify webhook signature.

        Returns:
            Error/skip result dict, or None if signature is valid
        """
        if not signature:
            logger.warning("No signature header in webhook ingress message")
            return None

        try:
            webhook_secret = await self._deps.get_webhook_secret()
            if not self._deps.verify_signature(body_str, signature, webhook_secret):
                logger.error("Invalid signature for delivery %s", delivery_id)
                self._deps.publish_metric("InvalidSignature", 1.0, "Count")
                return {"success": True, "skipped": True, "reason": "invalid_signature"}
        except (ValueError, TypeError, RuntimeError) as err:
            logger.error("Cannot verify signature: %s", str(err))
            return {"success": False, "error": str(err)}

        return None

    def _route_workflow_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle a workflow_run event."""
        action = payload.get("action")
        workflow_run = payload.get("workflow_run", {})
        run_id = workflow_run.get("id")
        conclusion = workflow_run.get("conclusion")
        logger.info(
            "Workflow run %s %s (conclusion=%s)",
            run_id,
            action,
            conclusion,
        )
        return {"success": True, "routed": "acknowledged"}

    async def _route_event(
        self, github_event: str | None, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Route an event based on its type."""
        if github_event == "workflow_run":
            return self._route_workflow_run(payload)
        if github_event == "ping":
            logger.info("Received ping event via ingress queue")
            return {"success": True, "routed": "ping_acknowledged"}

        logger.info("Ignoring event type: %s", github_event)
        self._deps.enqueue_ignored(payload, f"event type {github_event} ignored")
        return {"success": True, "routed": "ignored_events"}

    def extract_headers_and_body(
        self, record: dict[str, Any]
    ) -> tuple[dict[str, str], str, dict[str, Any] | None]:
        """Extract headers and body from an SQS record.

        Returns:
            Tuple of (headers dict, raw body string, parsed payload or None)
        """
        raw_body = record.get("body", "")

        headers: dict[str, str] = {}
        for header_name in (
            "x-github-event",
            "x-hub-signature-256",
            "x-github-delivery",
        ):
            value = get_message_attribute(record, header_name)
            if value is not None:
                headers[header_name] = value

        payload: dict[str, Any] | None = None
        try:
            payload = json.loads(raw_body)
        except (json.JSONDecodeError, TypeError):
            payload = None

        return headers, raw_body, payload

    async def handle(self, record: dict[str, Any]) -> dict[str, Any]:
        """Handle a single SQS record.

        Args:
            record: SQS record dictionary

        Returns:
            Result dictionary with success, routed/skipped, and optional error
        """
        start_time = time.time()

        headers, body_str, payload = self.extract_headers_and_body(record)
        github_event = headers.get("x-github-event")
        signature = headers.get("x-hub-signature-256")
        delivery_id = headers.get("x-github-delivery")

        logger.info(
            "Processing webhook ingress: event=%s, delivery=%s",
            github_event,
            delivery_id,
        )

        sig_error = await self._verify_signature(body_str, signature, delivery_id)
        if sig_error:
            return sig_error

        if delivery_id and await self._deps.check_idempotency(delivery_id):
            logger.info("Duplicate webhook delivery %s detected", delivery_id)
            return {"success": True, "skipped": True, "reason": "duplicate"}

        if payload is None:
            logger.error("Failed to parse webhook body")
            return {"success": True, "skipped": True, "reason": "invalid_json"}

        elapsed_ms = (time.time() - start_time) * 1000
        self._deps.publish_metric(
            "WebhookIngressProcessingTime", elapsed_ms, "Milliseconds"
        )
        return await self._route_event(github_event, payload)
