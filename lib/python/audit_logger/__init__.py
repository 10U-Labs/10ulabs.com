"""Audit logging and write-ahead durability for API endpoints.

This module provides:
- WriteAheadLogger: Class for write-ahead logging to SQS and DynamoDB audit trails
- audit_request: Decorator for automatic audit logging of Lambda handlers
- redact_payload: Function to remove sensitive data from payloads before logging
"""
import base64
import datetime
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Default fields to redact from payloads
DEFAULT_REDACT_FIELDS = [
    'password',
    'token',
    'secret',
    'api_key',
    'apikey',
    'authorization',
    'registration_token',
    'github_token',
    'recaptcha_token',
    'webhook_secret',
    'credential',
]

# Singleton clients for reuse across invocations
_clients: Dict[str, Any] = {'sqs': None, 'dynamodb': None}


def _get_sqs_client():
    """Get or create cached SQS client."""
    if _clients['sqs'] is None:
        _clients['sqs'] = boto3.client('sqs')
    return _clients['sqs']


def _get_dynamodb_client():
    """Get or create cached DynamoDB client."""
    if _clients['dynamodb'] is None:
        _clients['dynamodb'] = boto3.client('dynamodb')
    return _clients['dynamodb']


@dataclass
class AuditRecord:
    """Represents an audit log entry for an API request.

    Attributes:
        request_id: Unique identifier for the request.
        endpoint: Name of the API endpoint.
        method: HTTP method (GET, POST, etc.).
        status: Current status (received, processing, completed, failed, abandoned).
        request_timestamp: ISO timestamp when request was received.
        request_payload: Redacted request body.
        metadata: Additional fields (source_ip, user_agent, correlation_id,
                  completion_timestamp, response_code, error_message, reprocess_count).
    """
    request_id: str
    endpoint: str
    method: str
    status: str
    request_timestamp: str
    request_payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def source_ip(self) -> str:
        """Get source IP from metadata."""
        return self.metadata.get('source_ip', '')

    @property
    def user_agent(self) -> str:
        """Get user agent from metadata."""
        return self.metadata.get('user_agent', '')

    @property
    def correlation_id(self) -> str:
        """Get correlation ID from metadata."""
        return self.metadata.get('correlation_id', '')

    @property
    def completion_timestamp(self) -> str:
        """Get completion timestamp from metadata."""
        return self.metadata.get('completion_timestamp', '')

    @property
    def response_code(self) -> int:
        """Get response code from metadata."""
        return self.metadata.get('response_code', 0)

    @property
    def error_message(self) -> str:
        """Get error message from metadata."""
        return self.metadata.get('error_message', '')

    @property
    def reprocess_count(self) -> int:
        """Get reprocess count from metadata."""
        return self.metadata.get('reprocess_count', 0)

    @property
    def ttl(self) -> int:
        """Calculate TTL (90 days from request timestamp)."""
        try:
            dt = datetime.datetime.fromisoformat(self.request_timestamp.replace('Z', '+00:00'))
            return int(dt.timestamp()) + (90 * 24 * 60 * 60)
        except (ValueError, AttributeError):
            return int(time.time()) + (90 * 24 * 60 * 60)

    @property
    def endpoint_timestamp(self) -> str:
        """Generate sort key for DynamoDB."""
        return f"{self.endpoint}#{self.request_timestamp}"


def redact_payload(payload: Any, redact_fields: Optional[List[str]] = None) -> Any:
    """Recursively redact sensitive fields from a payload.

    Args:
        payload: The payload to redact (dict, list, or primitive).
        redact_fields: List of field names to redact (case-insensitive).

    Returns:
        A copy of the payload with sensitive fields replaced with '[REDACTED]'.
    """
    if redact_fields is None:
        redact_fields = DEFAULT_REDACT_FIELDS

    redact_set = {f.lower() for f in redact_fields}

    if isinstance(payload, dict):
        result = {}
        for key, value in payload.items():
            if key.lower() in redact_set:
                result[key] = '[REDACTED]'
            else:
                result[key] = redact_payload(value, redact_fields)
        return result
    if isinstance(payload, list):
        return [redact_payload(item, redact_fields) for item in payload]
    return payload


class WriteAheadLogger:
    """Handles write-ahead logging to SQS and DynamoDB audit trails.

    This class implements the write-ahead logging pattern for API endpoints:
    1. Write request to SQS (durability)
    2. Write to DynamoDB audit table (status=received)
    3. Update status to 'processing'
    4. After processing: update status to 'completed' or 'failed'
    """

    def __init__(
        self,
        audit_table_name: str,
        write_ahead_queue_url: Optional[str] = None,
        endpoint_name: str = 'unknown',
        redact_fields: Optional[List[str]] = None
    ):
        """Initialize the WriteAheadLogger.

        Args:
            audit_table_name: Name of the DynamoDB audit table.
            write_ahead_queue_url: URL of the SQS write-ahead queue (optional).
            endpoint_name: Name of the endpoint for logging.
            redact_fields: Additional fields to redact from payloads.
        """
        self.audit_table_name = audit_table_name
        self.write_ahead_queue_url = write_ahead_queue_url
        self.endpoint_name = endpoint_name
        self.redact_fields = (redact_fields or []) + DEFAULT_REDACT_FIELDS

    def extract_request_info(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract request information from Lambda event."""
        headers = event.get('headers', {}) or {}
        request_context = event.get('requestContext', {}) or {}
        http_context = request_context.get('http', {}) or {}
        identity = request_context.get('identity', {}) or {}

        # Case-insensitive header lookup
        def get_header(name: str) -> str:
            for key, value in headers.items():
                if key.lower() == name.lower():
                    return value or ''
            return ''

        return {
            'method': event.get('httpMethod') or http_context.get('method', 'UNKNOWN'),
            'source_ip': identity.get('sourceIp') or http_context.get('sourceIp', ''),
            'user_agent': get_header('user-agent'),
            'correlation_id': get_header('x-correlation-id') or get_header('x-request-id') or '',
        }

    def parse_body(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Parse request body from Lambda event."""
        body = event.get('body', '')
        if not body:
            return {}

        try:
            if event.get('isBase64Encoded'):
                body = base64.b64decode(body).decode('utf-8')
            return json.loads(body)
        except (json.JSONDecodeError, ValueError):
            return {'_raw': body[:1000]}  # Truncate raw body

    def log_request_received(self, event: Dict[str, Any]) -> AuditRecord:
        """Log that a request was received (Step 1 & 2).

        Writes to SQS for durability, then writes to DynamoDB with status='received'.

        Args:
            event: The Lambda event object.

        Returns:
            AuditRecord with the request details.
        """
        request_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now(datetime.UTC).isoformat()
        request_info = self.extract_request_info(event)
        raw_payload = self.parse_body(event)
        redacted_payload = redact_payload(raw_payload, self.redact_fields)

        record = AuditRecord(
            request_id=request_id,
            endpoint=self.endpoint_name,
            method=request_info['method'],
            status='received',
            request_timestamp=timestamp,
            request_payload=redacted_payload,
            metadata={
                'source_ip': request_info['source_ip'],
                'user_agent': request_info['user_agent'],
                'correlation_id': request_info['correlation_id'],
            }
        )

        # Step 1: Write to SQS for durability (if configured)
        if self.write_ahead_queue_url:
            self._write_to_sqs(record, event)

        # Step 2: Write to DynamoDB audit table
        self._write_to_dynamodb(record)

        return record

    def log_processing_started(self, record: AuditRecord) -> None:
        """Update status to 'processing' (Step 3).

        Args:
            record: The AuditRecord to update.
        """
        record.status = 'processing'
        self._update_status(record)

    def log_completed(self, record: AuditRecord, response_code: int) -> None:
        """Update status to 'completed' (Step 4 - success).

        Args:
            record: The AuditRecord to update.
            response_code: The HTTP response code.
        """
        record.status = 'completed'
        record.metadata['response_code'] = response_code
        record.metadata['completion_timestamp'] = datetime.datetime.now(datetime.UTC).isoformat()
        self._update_status(record)

    def log_failed(self, record: AuditRecord, error: str, response_code: int) -> None:
        """Update status to 'failed' (Step 4 - failure).

        Args:
            record: The AuditRecord to update.
            error: Error message.
            response_code: The HTTP response code.
        """
        record.status = 'failed'
        record.metadata['error_message'] = error[:1000]  # Truncate error message
        record.metadata['response_code'] = response_code
        record.metadata['completion_timestamp'] = datetime.datetime.now(datetime.UTC).isoformat()
        self._update_status(record)

    def _write_to_sqs(self, record: AuditRecord, original_event: Dict[str, Any]) -> None:
        """Write request to SQS for durability."""
        try:
            sqs = _get_sqs_client()
            message_body = json.dumps({
                'request_id': record.request_id,
                'endpoint': record.endpoint,
                'method': record.method,
                'timestamp': record.request_timestamp,
                'event': original_event,
            })
            sqs.send_message(
                QueueUrl=self.write_ahead_queue_url,
                MessageBody=message_body,
            )
            logger.debug("Wrote request %s to write-ahead queue", record.request_id)
        except ClientError as e:
            logger.warning("Failed to write to SQS write-ahead queue: %s", e)
            # Continue without SQS - DynamoDB is still written

    def _write_to_dynamodb(self, record: AuditRecord) -> None:
        """Write audit record to DynamoDB."""
        try:
            dynamodb = _get_dynamodb_client()
            item = {
                'request_id': {'S': record.request_id},
                'endpoint_timestamp': {'S': record.endpoint_timestamp},
                'endpoint': {'S': record.endpoint},
                'method': {'S': record.method},
                'status': {'S': record.status},
                'request_timestamp': {'S': record.request_timestamp},
                'request_payload': {'S': json.dumps(record.request_payload)},
                'source_ip': {'S': record.source_ip},
                'user_agent': {'S': record.user_agent},
                'correlation_id': {'S': record.correlation_id},
                'ttl': {'N': str(record.ttl)},
            }
            dynamodb.put_item(TableName=self.audit_table_name, Item=item)
            logger.debug("Wrote audit record %s to DynamoDB", record.request_id)
        except ClientError as e:
            logger.error("Failed to write audit record to DynamoDB: %s", e)
            raise

    def _update_status(self, record: AuditRecord) -> None:
        """Update audit record status in DynamoDB."""
        try:
            dynamodb = _get_dynamodb_client()
            update_expr = 'SET #status = :status'
            expr_values: Dict[str, Any] = {':status': {'S': record.status}}
            expr_names = {'#status': 'status'}

            if record.completion_timestamp:
                update_expr += ', completion_timestamp = :ct'
                expr_values[':ct'] = {'S': record.completion_timestamp}

            if record.response_code:
                update_expr += ', response_code = :rc'
                expr_values[':rc'] = {'N': str(record.response_code)}

            if record.error_message:
                update_expr += ', error_message = :em'
                expr_values[':em'] = {'S': record.error_message}

            dynamodb.update_item(
                TableName=self.audit_table_name,
                Key={
                    'request_id': {'S': record.request_id},
                    'endpoint_timestamp': {'S': record.endpoint_timestamp},
                },
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
            )
            logger.debug("Updated audit record %s status to %s", record.request_id, record.status)
        except ClientError as e:
            logger.error("Failed to update audit record status: %s", e)
            # Don't raise - status update failure shouldn't fail the request


def audit_request(
    endpoint_name: str,
    redact_fields: Optional[List[str]] = None,
    enabled_env_var: str = 'AUDIT_ENABLED'
) -> Callable:
    """Decorator for automatic audit logging of Lambda handlers.

    Usage:
        @audit_request('my-endpoint', redact_fields=['email'])
        def lambda_handler(event, context):
            return {'statusCode': 200, 'body': '...'}

    Args:
        endpoint_name: Name of the endpoint for logging.
        redact_fields: Additional fields to redact from payloads.
        enabled_env_var: Environment variable to check if audit is enabled.

    Returns:
        Decorated function with automatic audit logging.
    """
    def decorator(handler_func: Callable) -> Callable:
        @wraps(handler_func)
        def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
            # Check if audit is enabled
            audit_enabled = os.environ.get(enabled_env_var, 'true').lower() == 'true'
            audit_table = os.environ.get('AUDIT_TABLE_NAME')
            write_ahead_queue = os.environ.get('WRITE_AHEAD_QUEUE_URL')

            if not audit_enabled or not audit_table:
                # Audit disabled or not configured - just run the handler
                return handler_func(event, context)

            # Initialize logger
            audit_logger = WriteAheadLogger(
                audit_table_name=audit_table,
                write_ahead_queue_url=write_ahead_queue,
                endpoint_name=endpoint_name,
                redact_fields=redact_fields,
            )

            # Log request received
            record = audit_logger.log_request_received(event)

            try:
                # Log processing started
                audit_logger.log_processing_started(record)

                # Execute the handler
                response = handler_func(event, context)

                # Log completion
                response_code = response.get('statusCode', 200)
                if response_code < 400:
                    audit_logger.log_completed(record, response_code)
                else:
                    error_body = response.get('body', '')
                    audit_logger.log_failed(record, error_body, response_code)

                return response

            except Exception as e:
                # Log failure
                audit_logger.log_failed(record, str(e), 500)
                raise

        return wrapper
    return decorator


# Convenience function to get a configured logger from environment
def get_write_ahead_logger(
    endpoint_name: str,
    redact_fields: Optional[List[str]] = None
) -> WriteAheadLogger:
    """Get a WriteAheadLogger configured from environment variables.

    Environment variables:
        AUDIT_TABLE_NAME: Name of the DynamoDB audit table.
        WRITE_AHEAD_QUEUE_URL: URL of the SQS write-ahead queue.

    Args:
        endpoint_name: Name of the endpoint for logging.
        redact_fields: Additional fields to redact from payloads.

    Returns:
        Configured WriteAheadLogger instance.
    """
    return WriteAheadLogger(
        audit_table_name=os.environ.get('AUDIT_TABLE_NAME', ''),
        write_ahead_queue_url=os.environ.get('WRITE_AHEAD_QUEUE_URL'),
        endpoint_name=endpoint_name,
        redact_fields=redact_fields,
    )
