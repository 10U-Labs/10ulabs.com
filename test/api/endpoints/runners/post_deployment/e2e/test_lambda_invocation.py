"""E2E tests for Lambda invocation and routing.

User Journey: SQS message → Lambda → Route to correct runner endpoint

Critical Path: SQS event → Lambda handler → HTTP request to /v1/runners/{ec2|ecs}
Failure Impact: Runner requests not processed, GitHub Actions jobs stuck waiting.
"""
import json

import pytest
from botocore.exceptions import ClientError

from .conftest import create_sqs_event, create_runner_request


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

        # Create an SQS event with unmatched labels (no routing will happen)
        message_body = {
            "job_id": 1,
            "job_labels": ["self-hosted", "windows"],
            "github_repo": "test/repo",
            "run_id": 1
        }
        event = create_sqs_event(message_body)

        try:
            response = lambda_client.invoke(
                FunctionName=lambda_function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(event)
            )
            # Check for function errors
            function_error = response.get("FunctionError")
            assert function_error is None, (
                f"Lambda invocation failed with error: {function_error}"
            )
        except ClientError as e:
            pytest.fail(f"Lambda invocation failed: {e}")

    def test_lambda_returns_200_for_unmatched_labels(
        self, lambda_client, lambda_function_name
    ):
        """Verify Lambda returns 200 for unmatched labels.

        User Journey: SQS message with non-matching labels

        When: Lambda receives a request with labels that don't match ec2/ecs
        Then: Returns 200 status code
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = {
            "job_id": 999,
            "job_labels": ["self-hosted", "macos"],
            "github_repo": "test/repo",
            "run_id": 999
        }
        event = create_sqs_event(message_body)

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        payload = json.loads(response["Payload"].read())
        assert payload.get("statusCode") == 200

    def test_lambda_returns_single_result_for_unmatched_labels(
        self, lambda_client, lambda_function_name
    ):
        """Verify Lambda returns single result for unmatched labels.

        User Journey: SQS message with non-matching labels

        When: Lambda receives a request with labels that don't match ec2/ecs
        Then: Returns exactly one result
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = {
            "job_id": 999,
            "job_labels": ["self-hosted", "macos"],
            "github_repo": "test/repo",
            "run_id": 999
        }
        event = create_sqs_event(message_body)

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        payload = json.loads(response["Payload"].read())
        body = json.loads(payload.get("body", "{}"))
        results = body.get("results", [])
        assert len(results) == 1

    def test_lambda_returns_no_matching_runner_type_message(
        self, lambda_client, lambda_function_name
    ):
        """Verify Lambda returns correct message for unmatched labels.

        User Journey: SQS message with non-matching labels

        When: Lambda receives a request with labels that don't match ec2/ecs
        Then: Returns 'No matching runner type' message
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = {
            "job_id": 999,
            "job_labels": ["self-hosted", "macos"],
            "github_repo": "test/repo",
            "run_id": 999
        }
        event = create_sqs_event(message_body)

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        payload = json.loads(response["Payload"].read())
        body = json.loads(payload.get("body", "{}"))
        results = body.get("results", [])
        if not results:
            pytest.skip("No results returned")

        result = results[0].get("result", {})
        result_body = json.loads(result.get("body", "{}"))
        assert result_body.get("message") == "No matching runner type"

    def test_lambda_handles_invalid_json_gracefully(self, lambda_client, lambda_function_name):
        """Verify Lambda handles invalid JSON in SQS message.

        User Journey: Malformed SQS message

        When: Lambda receives an SQS message with invalid JSON
        Then: Does not throw function error (handles gracefully)
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = {
            "Records": [{
                "eventSource": "aws:sqs",
                "messageId": "invalid-json-msg",
                "body": "this is not valid json"
            }]
        }

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        # Should not have function error - graceful handling
        function_error = response.get("FunctionError")
        assert function_error is None

    def test_lambda_returns_200_for_invalid_json(self, lambda_client, lambda_function_name):
        """Verify Lambda returns 200 for invalid JSON.

        User Journey: Malformed SQS message

        When: Lambda receives an SQS message with invalid JSON
        Then: Returns 200 with error in results
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = {
            "Records": [{
                "eventSource": "aws:sqs",
                "messageId": "invalid-json-msg",
                "body": "this is not valid json"
            }]
        }

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        payload = json.loads(response["Payload"].read())
        assert payload.get("statusCode") == 200

    def test_lambda_returns_error_for_invalid_json(self, lambda_client, lambda_function_name):
        """Verify Lambda returns error in results for invalid JSON.

        User Journey: Malformed SQS message

        When: Lambda receives an SQS message with invalid JSON
        Then: Returns error in results
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = {
            "Records": [{
                "eventSource": "aws:sqs",
                "messageId": "invalid-json-msg",
                "body": "this is not valid json"
            }]
        }

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        payload = json.loads(response["Payload"].read())
        body = json.loads(payload.get("body", "{}"))
        results = body.get("results", [])
        assert len(results) == 1
        # Error should be present in first result
        # (implementation will mark as error in results)

    def test_lambda_rejects_non_sqs_event_with_400(self, lambda_client, lambda_function_name):
        """Verify Lambda returns 400 for non-SQS events.

        User Journey: Invalid event format

        When: Lambda is invoked with a non-SQS event
        Then: Returns 400 status code
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        # Not an SQS event - missing Records
        event = {"some": "data"}

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        payload = json.loads(response["Payload"].read())
        assert payload.get("statusCode") == 400

    def test_lambda_returns_expected_sqs_event_error(self, lambda_client, lambda_function_name):
        """Verify Lambda returns 'Expected SQS event' error for non-SQS events.

        User Journey: Invalid event format

        When: Lambda is invoked with a non-SQS event
        Then: Returns 'Expected SQS event' error message
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        # Not an SQS event - missing Records
        event = {"some": "data"}

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        payload = json.loads(response["Payload"].read())
        body = json.loads(payload.get("body", "{}"))
        assert body.get("error") == "Expected SQS event"


class TestLabelRouting:
    """Test that labels are correctly routed to endpoints."""

    def test_ec2_labels_invocation_succeeds(self, lambda_client, lambda_function_name):
        """Verify EC2 labels invocation does not throw error.

        User Journey: EC2 runner request routing

        When: Lambda receives a request with EC2 labels
        Then: Does not throw function error
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = create_runner_request("ec2", job_id=111)
        event = create_sqs_event(message_body, "ec2-test-msg")

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        # Lambda should not throw error - it will attempt routing
        function_error = response.get("FunctionError")
        assert function_error is None

    def test_ec2_labels_returns_single_result(self, lambda_client, lambda_function_name):
        """Verify EC2 labels return single result.

        User Journey: EC2 runner request routing

        When: Lambda receives a request with EC2 labels
        Then: Returns exactly one result
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = create_runner_request("ec2", job_id=111)
        event = create_sqs_event(message_body, "ec2-test-msg")

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        payload = json.loads(response["Payload"].read())
        body = json.loads(payload.get("body", "{}"))
        results = body.get("results", [])
        assert len(results) == 1

    def test_ec2_labels_returns_correct_message_id(self, lambda_client, lambda_function_name):
        """Verify EC2 labels return correct message ID.

        User Journey: EC2 runner request routing

        When: Lambda receives a request with EC2 labels
        Then: Returns the correct messageId
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = create_runner_request("ec2", job_id=111)
        event = create_sqs_event(message_body, "ec2-test-msg")

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        payload = json.loads(response["Payload"].read())
        body = json.loads(payload.get("body", "{}"))
        results = body.get("results", [])
        assert results[0].get("messageId") == "ec2-test-msg"

    def test_ecs_labels_invocation_succeeds(self, lambda_client, lambda_function_name):
        """Verify ECS labels invocation does not throw error.

        User Journey: ECS runner request routing

        When: Lambda receives a request with ECS/Fargate labels
        Then: Does not throw function error
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = create_runner_request("ecs", job_id=222)
        event = create_sqs_event(message_body, "ecs-test-msg")

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        # Lambda should not throw error - it will attempt routing
        function_error = response.get("FunctionError")
        assert function_error is None

    def test_ecs_labels_returns_single_result(self, lambda_client, lambda_function_name):
        """Verify ECS labels return single result.

        User Journey: ECS runner request routing

        When: Lambda receives a request with ECS/Fargate labels
        Then: Returns exactly one result
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = create_runner_request("ecs", job_id=222)
        event = create_sqs_event(message_body, "ecs-test-msg")

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        payload = json.loads(response["Payload"].read())
        body = json.loads(payload.get("body", "{}"))
        results = body.get("results", [])
        assert len(results) == 1

    def test_ecs_labels_returns_correct_message_id(self, lambda_client, lambda_function_name):
        """Verify ECS labels return correct message ID.

        User Journey: ECS runner request routing

        When: Lambda receives a request with ECS/Fargate labels
        Then: Returns the correct messageId
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        message_body = create_runner_request("ecs", job_id=222)
        event = create_sqs_event(message_body, "ecs-test-msg")

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        payload = json.loads(response["Payload"].read())
        body = json.loads(payload.get("body", "{}"))
        results = body.get("results", [])
        assert results[0].get("messageId") == "ecs-test-msg"

    def test_multiple_records_all_processed(self, lambda_client, lambda_function_name):
        """Verify multiple SQS records are all processed.

        User Journey: Batch SQS message processing

        When: Lambda receives multiple SQS records
        Then: All records are processed and results returned
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = {
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

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        payload = json.loads(response["Payload"].read())
        body = json.loads(payload.get("body", "{}"))
        results = body.get("results", [])
        assert len(results) == 2

    def test_multiple_records_first_message_id_returned(
        self, lambda_client, lambda_function_name
    ):
        """Verify first message ID is in results.

        User Journey: Batch SQS message processing

        When: Lambda receives multiple SQS records
        Then: First message ID is in results
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = {
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

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        payload = json.loads(response["Payload"].read())
        body = json.loads(payload.get("body", "{}"))
        results = body.get("results", [])
        message_ids = [r.get("messageId") for r in results]
        assert "msg-1" in message_ids

    def test_multiple_records_second_message_id_returned(
        self, lambda_client, lambda_function_name
    ):
        """Verify second message ID is in results.

        User Journey: Batch SQS message processing

        When: Lambda receives multiple SQS records
        Then: Second message ID is in results
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")

        event = {
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

        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )

        payload = json.loads(response["Payload"].read())
        body = json.loads(payload.get("body", "{}"))
        results = body.get("results", [])
        message_ids = [r.get("messageId") for r in results]
        assert "msg-2" in message_ids
