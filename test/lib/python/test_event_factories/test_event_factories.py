"""Comprehensive tests for event_factories module."""
import json

from event_factories import (
    create_workflow_job_event,
    workflow_job_event_factory,
    create_sqs_event,
    sqs_event_factory,
    create_dlq_message,
    dlq_message_factory,
    create_circuit_breaker_closed_state,
    create_circuit_breaker_open_state,
    create_ecs_runner_post_event,
)


# === create_workflow_job_event ===


class TestCreateWorkflowJobEvent:
    """Tests for create_workflow_job_event function."""

    def test_returns_dict(self):
        """create_workflow_job_event returns a dictionary."""
        result = create_workflow_job_event()
        assert isinstance(result, dict)

    def test_has_correct_path(self):
        """create_workflow_job_event has correct path."""
        result = create_workflow_job_event()
        assert result["path"] == "/v1/runners"

    def test_has_correct_http_method(self):
        """create_workflow_job_event has POST method."""
        result = create_workflow_job_event()
        assert result["httpMethod"] == "POST"

    def test_has_github_event_header(self):
        """create_workflow_job_event has X-GitHub-Event header."""
        result = create_workflow_job_event()
        assert result["headers"]["X-GitHub-Event"] == "workflow_job"

    def test_has_signature_header(self):
        """create_workflow_job_event has X-Hub-Signature-256 header."""
        result = create_workflow_job_event()
        assert "X-Hub-Signature-256" in result["headers"]

    def test_default_action_is_queued(self):
        """create_workflow_job_event default action is 'queued'."""
        result = create_workflow_job_event()
        body = json.loads(result["body"])
        assert body["action"] == "queued"

    def test_custom_action(self):
        """create_workflow_job_event uses custom action."""
        result = create_workflow_job_event(action="completed")
        body = json.loads(result["body"])
        assert body["action"] == "completed"

    def test_default_job_id(self):
        """create_workflow_job_event default job_id is 123."""
        result = create_workflow_job_event()
        body = json.loads(result["body"])
        assert body["workflow_job"]["id"] == 123

    def test_custom_job_id(self):
        """create_workflow_job_event uses custom job_id."""
        result = create_workflow_job_event(job_id=456)
        body = json.loads(result["body"])
        assert body["workflow_job"]["id"] == 456

    def test_default_labels(self):
        """create_workflow_job_event default labels are self-hosted and linux."""
        result = create_workflow_job_event()
        body = json.loads(result["body"])
        assert body["workflow_job"]["labels"] == ["self-hosted", "linux"]

    def test_custom_labels(self):
        """create_workflow_job_event uses custom labels."""
        result = create_workflow_job_event(labels=["ecs", "arm64"])
        body = json.loads(result["body"])
        assert body["workflow_job"]["labels"] == ["ecs", "arm64"]

    def test_default_repo(self):
        """create_workflow_job_event default repo is test/repo."""
        result = create_workflow_job_event()
        body = json.loads(result["body"])
        assert body["repository"]["full_name"] == "test/repo"

    def test_custom_repo(self):
        """create_workflow_job_event uses custom repo."""
        result = create_workflow_job_event(repo="owner/name")
        body = json.loads(result["body"])
        assert body["repository"]["full_name"] == "owner/name"

    def test_run_id_in_body(self):
        """create_workflow_job_event includes run_id in body."""
        result = create_workflow_job_event(run_id=789)
        body = json.loads(result["body"])
        assert body["workflow_job"]["run_id"] == 789


# === workflow_job_event_factory ===


class TestWorkflowJobEventFactory:
    """Tests for workflow_job_event_factory function."""

    def test_returns_callable(self):
        """workflow_job_event_factory returns a callable."""
        factory = workflow_job_event_factory()
        assert callable(factory)

    def test_factory_creates_event_with_path(self):
        """workflow_job_event_factory creates event with path."""
        factory = workflow_job_event_factory()
        result = factory()
        assert "path" in result

    def test_factory_creates_event_with_body(self):
        """workflow_job_event_factory creates event with body."""
        factory = workflow_job_event_factory()
        result = factory()
        assert "body" in result


# === create_sqs_event ===


class TestCreateSqsEvent:
    """Tests for create_sqs_event function."""

    def test_returns_dict(self):
        """create_sqs_event returns a dictionary."""
        result = create_sqs_event()
        assert isinstance(result, dict)

    def test_has_records_key(self):
        """create_sqs_event has Records key."""
        result = create_sqs_event()
        assert "Records" in result

    def test_default_has_one_record(self):
        """create_sqs_event default has one record."""
        result = create_sqs_event()
        assert len(result["Records"]) == 1

    def test_default_record_has_message_id(self):
        """create_sqs_event default record has messageId."""
        result = create_sqs_event()
        assert result["Records"][0]["messageId"] == "test-message-id"

    def test_default_record_has_body(self):
        """create_sqs_event default record has body."""
        result = create_sqs_event()
        body = json.loads(result["Records"][0]["body"])
        assert body["job_id"] == 123

    def test_custom_records(self):
        """create_sqs_event uses custom records."""
        custom = [{"messageId": "custom", "body": "{}"}]
        result = create_sqs_event(records=custom)
        assert result["Records"][0]["messageId"] == "custom"


# === sqs_event_factory ===


class TestSqsEventFactory:
    """Tests for sqs_event_factory function."""

    def test_returns_callable(self):
        """sqs_event_factory returns a callable."""
        factory = sqs_event_factory()
        assert callable(factory)

    def test_factory_creates_event(self):
        """sqs_event_factory creates valid events."""
        factory = sqs_event_factory()
        result = factory()
        assert "Records" in result


# === create_dlq_message ===


class TestCreateDlqMessage:
    """Tests for create_dlq_message function."""

    def test_returns_dict(self):
        """create_dlq_message returns a dictionary."""
        result = create_dlq_message()
        assert isinstance(result, dict)

    def test_has_message_id(self):
        """create_dlq_message has MessageId."""
        result = create_dlq_message()
        assert result["MessageId"] == "test-message-id"

    def test_has_receipt_handle(self):
        """create_dlq_message has ReceiptHandle."""
        result = create_dlq_message()
        assert result["ReceiptHandle"] == "test-receipt"

    def test_custom_receipt_handle(self):
        """create_dlq_message uses custom receipt_handle."""
        result = create_dlq_message(receipt_handle="custom-receipt")
        assert result["ReceiptHandle"] == "custom-receipt"

    def test_default_body(self):
        """create_dlq_message default body has job_id."""
        result = create_dlq_message()
        body = json.loads(result["Body"])
        assert body["job_id"] == 123

    def test_custom_body(self):
        """create_dlq_message uses custom body."""
        result = create_dlq_message(body={"custom": "data"})
        body = json.loads(result["Body"])
        assert body["custom"] == "data"

    def test_default_attributes(self):
        """create_dlq_message has default attributes."""
        result = create_dlq_message()
        assert result["Attributes"]["ApproximateReceiveCount"] == "1"

    def test_custom_attributes(self):
        """create_dlq_message uses custom attributes."""
        result = create_dlq_message(attributes={"Custom": "value"})
        assert result["Attributes"]["Custom"] == "value"


# === dlq_message_factory ===


class TestDlqMessageFactory:
    """Tests for dlq_message_factory function."""

    def test_returns_callable(self):
        """dlq_message_factory returns a callable."""
        factory = dlq_message_factory()
        assert callable(factory)

    def test_factory_creates_message(self):
        """dlq_message_factory creates valid messages."""
        factory = dlq_message_factory()
        result = factory()
        assert "MessageId" in result


# === create_circuit_breaker_closed_state ===


class TestCreateCircuitBreakerClosedState:
    """Tests for create_circuit_breaker_closed_state function."""

    def test_returns_dict(self):
        """create_circuit_breaker_closed_state returns a dictionary."""
        result = create_circuit_breaker_closed_state()
        assert isinstance(result, dict)

    def test_state_is_closed(self):
        """create_circuit_breaker_closed_state state is 'closed'."""
        result = create_circuit_breaker_closed_state()
        assert result["state"] == "closed"

    def test_failure_count_is_zero(self):
        """create_circuit_breaker_closed_state failure_count is 0."""
        result = create_circuit_breaker_closed_state()
        assert result["failure_count"] == 0

    def test_last_failure_time_is_none(self):
        """create_circuit_breaker_closed_state last_failure_time is None."""
        result = create_circuit_breaker_closed_state()
        assert result["last_failure_time"] is None


# === create_circuit_breaker_open_state ===


class TestCreateCircuitBreakerOpenState:
    """Tests for create_circuit_breaker_open_state function."""

    def test_returns_dict(self):
        """create_circuit_breaker_open_state returns a dictionary."""
        result = create_circuit_breaker_open_state()
        assert isinstance(result, dict)

    def test_state_is_open(self):
        """create_circuit_breaker_open_state state is 'open'."""
        result = create_circuit_breaker_open_state()
        assert result["state"] == "open"

    def test_failure_count_is_five(self):
        """create_circuit_breaker_open_state failure_count is 5."""
        result = create_circuit_breaker_open_state()
        assert result["failure_count"] == 5

    def test_last_failure_time_is_set(self):
        """create_circuit_breaker_open_state last_failure_time is not None."""
        result = create_circuit_breaker_open_state()
        assert result["last_failure_time"] is not None

    def test_last_failure_time_is_float(self):
        """create_circuit_breaker_open_state last_failure_time is float."""
        result = create_circuit_breaker_open_state()
        assert isinstance(result["last_failure_time"], float)


# === create_ecs_runner_post_event ===


class TestCreateEcsRunnerPostEvent:
    """Tests for create_ecs_runner_post_event function."""

    def test_returns_dict(self):
        """create_ecs_runner_post_event returns a dictionary."""
        result = create_ecs_runner_post_event()
        assert isinstance(result, dict)

    def test_has_correct_path(self):
        """create_ecs_runner_post_event has correct path."""
        result = create_ecs_runner_post_event()
        assert result["path"] == "/v1/runners/ecs"

    def test_has_post_method(self):
        """create_ecs_runner_post_event has POST method."""
        result = create_ecs_runner_post_event()
        assert result["httpMethod"] == "POST"

    def test_default_job_id(self):
        """create_ecs_runner_post_event default job_id is 123."""
        result = create_ecs_runner_post_event()
        body = json.loads(result["body"])
        assert body["job_id"] == 123

    def test_custom_job_id(self):
        """create_ecs_runner_post_event uses custom job_id."""
        result = create_ecs_runner_post_event(job_id=999)
        body = json.loads(result["body"])
        assert body["job_id"] == 999

    def test_default_job_labels(self):
        """create_ecs_runner_post_event default labels."""
        result = create_ecs_runner_post_event()
        body = json.loads(result["body"])
        assert body["job_labels"] == ["fargate", "self-hosted"]

    def test_custom_job_labels(self):
        """create_ecs_runner_post_event uses custom labels."""
        result = create_ecs_runner_post_event(job_labels=["custom"])
        body = json.loads(result["body"])
        assert body["job_labels"] == ["custom"]

    def test_default_github_repo(self):
        """create_ecs_runner_post_event default repo."""
        result = create_ecs_runner_post_event()
        body = json.loads(result["body"])
        assert body["github_repo"] == "test/repo"

    def test_custom_github_repo(self):
        """create_ecs_runner_post_event uses custom repo."""
        result = create_ecs_runner_post_event(github_repo="owner/name")
        body = json.loads(result["body"])
        assert body["github_repo"] == "owner/name"
