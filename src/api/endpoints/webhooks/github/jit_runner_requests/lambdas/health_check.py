"""Simple health check Lambda for JIT runner requests webhook service.

This is a lightweight liveness check with no external dependencies.
For circuit breaker status, use GET /v1/webhooks/github/jit-runner-requests/circuit-breaker.
"""

import json
import logging
import time
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Standard CORS headers for all responses
CORS_HEADERS = {"Access-Control-Allow-Origin": "*"}


def _build_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """Build a standard API response with JSON body and CORS headers."""
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {"Content-Type": "application/json", **CORS_HEADERS},
    }


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Handle health check requests.

    Returns a simple 200 OK with minimal overhead.
    No DynamoDB or other AWS service calls.
    """
    http_method = event.get("httpMethod", "GET")

    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "body": "",
            "headers": {
                **CORS_HEADERS,
                "Access-Control-Allow-Methods": "GET,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,X-Api-Key",
            },
        }

    if http_method == "GET":
        return _build_response(200, {
            "status": "healthy",
            "timestamp": int(time.time()),
            "service": "jit-runner-requests",
        })

    return _build_response(405, {
        "error": "Method not allowed",
        "allowed_methods": ["GET", "OPTIONS"],
    })
