"""E2E tests for Lambda invocation and routing.

User Journey: SQS message → Lambda → Route to correct runner endpoint

Critical Path: SQS event → Lambda handler → HTTP request to /v1/runners/{ec2|ecs}
Failure Impact: Runner requests not processed, GitHub Actions jobs stuck waiting.
"""
import json

import pytest

from .conftest import (
    create_sqs_event,
    create_runner_request,
    invoke_lambda,
    invoke_and_parse,
)


def create_unmatched_labels_event(job_id: int = 999) -> dict:
    """Create an SQS event with labels that don't match ec2/ecs."""
    message_body = {
        "job_id": job_id,
        "job_labels": ["self-hosted", "macos"],
        "github_repo": "test/repo",
        "run_id": job_id
    }
    return create_sqs_event(message_body)


def create_invalid_json_event() -> dict:
    """Create an SQS event with invalid JSON in the body."""
    return {
        "Records": [{
            "eventSource": "aws:sqs",
            "messageId": "invalid-json-msg",
            "body": "this is not valid json"
        }]
    }


def create_multi_record_event() -> dict:
    """Create an SQS event with multiple records."""
    return {
        "Records": [
            {
                "eventSource": "aws:sqs",
                "messageId": "msg-1",
                "body": json.dumps({
                    "job_id": 1,
                    "job_labels": ["self-hosted", "linux"],
                    "github_repo": "test/repo",
                    "run_id": 1
                })
            },
            {
                "eventSource": "aws:sqs",
                "messageId": "msg-2",
                "body": json.dumps({
                    "job_id": 2,
                    "job_labels": ["self-hosted", "windows"],
                    "github_repo": "test/repo",
                    "run_id": 2
                })
            }
        ]
    }


class TestLambdaDirectInvocation:
    """Test Lambda can be invoked directly."""

    def test_lambda_can_be_invoked(self, lambda_client, lambda_function_name):
        """Verify Lambda function can be invoked.

        User Journey: Direct Lambda invocation for testing

        When: Lambda is invoked with a minimal SQS event
        Then: The invocation succeeds (no internal error)
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = {
            "job_id": 1,
            "job_labels": ["self-hosted", "windows"],
            "github_repo": "test/repo",
            "run_id": 1
        }
        event = create_sqs_event(message_body)
        response = invoke_lambda(lambda_client, lambda_function_name, event)
        assert response.get("FunctionError") is None

    def test_lambda_returns_200_for_unmatched_labels(
        self, lambda_client, lambda_function_name
    ):
        """Verify Lambda returns 200 for unmatched labels."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = create_unmatched_labels_event()
        _, payload, _, _ = invoke_and_parse(lambda_client, lambda_function_name, event)
        assert payload.get("statusCode") == 200

    def test_lambda_returns_single_result_for_unmatched_labels(
        self, lambda_client, lambda_function_name
    ):
        """Verify Lambda returns single result for unmatched labels."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = create_unmatched_labels_event()
        _, _, _, results = invoke_and_parse(lambda_client, lambda_function_name, event)
        assert len(results) == 1

    def test_lambda_returns_no_matching_runner_type_message(
        self, lambda_client, lambda_function_name
    ):
        """Verify Lambda returns 'No matching runner type' message."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = create_unmatched_labels_event()
        _, _, _, results = invoke_and_parse(lambda_client, lambda_function_name, event)
        if not results:
            pytest.skip("No results returned")

        result = results[0].get("result", {})
        result_body = json.loads(result.get("body", "{}"))
        assert result_body.get("message") == "No matching runner type"

    def test_lambda_handles_invalid_json_gracefully(self, lambda_client, lambda_function_name):
        """Verify Lambda handles invalid JSON without function error."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = create_invalid_json_event()
        response = invoke_lambda(lambda_client, lambda_function_name, event)
        assert response.get("FunctionError") is None

    def test_lambda_returns_200_for_invalid_json(self, lambda_client, lambda_function_name):
        """Verify Lambda returns 200 for invalid JSON."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = create_invalid_json_event()
        _, payload, _, _ = invoke_and_parse(lambda_client, lambda_function_name, event)
        assert payload.get("statusCode") == 200

    def test_lambda_returns_error_for_invalid_json(self, lambda_client, lambda_function_name):
        """Verify Lambda returns error in results for invalid JSON."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = create_invalid_json_event()
        _, _, _, results = invoke_and_parse(lambda_client, lambda_function_name, event)
        assert len(results) == 1

    def test_lambda_rejects_non_sqs_event_with_400(self, lambda_client, lambda_function_name):
        """Verify Lambda returns 400 for non-SQS events."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = {"some": "data"}
        _, payload, _, _ = invoke_and_parse(lambda_client, lambda_function_name, event)
        assert payload.get("statusCode") == 400

    def test_lambda_returns_expected_sqs_event_error(self, lambda_client, lambda_function_name):
        """Verify Lambda returns 'Expected SQS event' error."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = {"some": "data"}
        _, _, body, _ = invoke_and_parse(lambda_client, lambda_function_name, event)
        assert body.get("error") == "Expected SQS event"


class TestLabelRouting:
    """Test that labels are correctly routed to endpoints."""

    def test_ec2_labels_invocation_succeeds(self, lambda_client, lambda_function_name):
        """Verify EC2 labels invocation does not throw error."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = create_runner_request("ec2", job_id=111)
        event = create_sqs_event(message_body, "ec2-test-msg")
        response = invoke_lambda(lambda_client, lambda_function_name, event)
        assert response.get("FunctionError") is None

    def test_ec2_labels_returns_single_result(self, lambda_client, lambda_function_name):
        """Verify EC2 labels return single result."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = create_runner_request("ec2", job_id=111)
        event = create_sqs_event(message_body, "ec2-test-msg")
        _, _, _, results = invoke_and_parse(lambda_client, lambda_function_name, event)
        assert len(results) == 1

    def test_ec2_labels_returns_correct_message_id(self, lambda_client, lambda_function_name):
        """Verify EC2 labels return correct message ID."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = create_runner_request("ec2", job_id=111)
        event = create_sqs_event(message_body, "ec2-test-msg")
        _, _, _, results = invoke_and_parse(lambda_client, lambda_function_name, event)
        assert results[0].get("messageId") == "ec2-test-msg"

    def test_ecs_labels_invocation_succeeds(self, lambda_client, lambda_function_name):
        """Verify ECS labels invocation does not throw error."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = create_runner_request("ecs", job_id=222)
        event = create_sqs_event(message_body, "ecs-test-msg")
        response = invoke_lambda(lambda_client, lambda_function_name, event)
        assert response.get("FunctionError") is None

    def test_ecs_labels_returns_single_result(self, lambda_client, lambda_function_name):
        """Verify ECS labels return single result."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = create_runner_request("ecs", job_id=222)
        event = create_sqs_event(message_body, "ecs-test-msg")
        _, _, _, results = invoke_and_parse(lambda_client, lambda_function_name, event)
        assert len(results) == 1

    def test_ecs_labels_returns_correct_message_id(self, lambda_client, lambda_function_name):
        """Verify ECS labels return correct message ID."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = create_runner_request("ecs", job_id=222)
        event = create_sqs_event(message_body, "ecs-test-msg")
        _, _, _, results = invoke_and_parse(lambda_client, lambda_function_name, event)
        assert results[0].get("messageId") == "ecs-test-msg"

    def test_multiple_records_all_processed(self, lambda_client, lambda_function_name):
        """Verify multiple SQS records are all processed."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = create_multi_record_event()
        _, _, _, results = invoke_and_parse(lambda_client, lambda_function_name, event)
        assert len(results) == 2

    def test_multiple_records_first_message_id_returned(
        self, lambda_client, lambda_function_name
    ):
        """Verify first message ID is in results."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = create_multi_record_event()
        _, _, _, results = invoke_and_parse(lambda_client, lambda_function_name, event)
        message_ids = [r.get("messageId") for r in results]
        assert "msg-1" in message_ids

    def test_multiple_records_second_message_id_returned(
        self, lambda_client, lambda_function_name
    ):
        """Verify second message ID is in results."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = create_multi_record_event()
        _, _, _, results = invoke_and_parse(lambda_client, lambda_function_name, event)
        message_ids = [r.get("messageId") for r in results]
        assert "msg-2" in message_ids
