"""Integration tests for runners Lambda package contents.

These tests verify that deployed Lambda packages work correctly at runtime.
Shared modules (runner_labels.js, etc/runners.json) are now in the Lambda Layer.
"""


def test_webhook_handler_returns_200_status(webhook_handler_response):
    """Verify webhook handler returns 200 status code."""
    assert webhook_handler_response["response"]["StatusCode"] == 200


def test_webhook_handler_no_module_not_found_error(webhook_handler_response):
    """Verify webhook handler does not fail with ModuleNotFoundError.

    If runner_labels import failed, we'd get a 500 with ModuleNotFoundError.
    A successful import means the Lambda could at least parse the labels.
    """
    payload = webhook_handler_response["payload"]
    error_msg = payload.get("errorMessage", "")

    assert "ModuleNotFoundError" not in error_msg
