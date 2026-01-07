"""Comprehensive tests for test_fixtures.unit module."""
import io
import json
import tempfile
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from test_fixtures.unit import (
    TEST_CONSTANTS,
    ENV_VAR_PRESETS,
    load_handler_module,
    parse_lambda_response_payload,
    create_mock_dynamodb_client,
    assert_no_hardcoded_env_defaults,
)
from terraform_config import TEST_AWS_REGION


# === TEST_CONSTANTS ===


class TestTestConstants:
    """Tests for TEST_CONSTANTS dictionary."""

    def test_has_queue_url_key(self):
        """TEST_CONSTANTS has 'queue_url' key."""
        assert 'queue_url' in TEST_CONSTANTS

    def test_has_dynamodb_table_key(self):
        """TEST_CONSTANTS has 'dynamodb_table' key."""
        assert 'dynamodb_table' in TEST_CONSTANTS

    def test_has_lambda_function_key(self):
        """TEST_CONSTANTS has 'lambda_function' key."""
        assert 'lambda_function' in TEST_CONSTANTS

    def test_has_instance_id_key(self):
        """TEST_CONSTANTS has 'instance_id' key."""
        assert 'instance_id' in TEST_CONSTANTS

    def test_has_instance_id_2_key(self):
        """TEST_CONSTANTS has 'instance_id_2' key."""
        assert 'instance_id_2' in TEST_CONSTANTS

    def test_has_instance_id_3_key(self):
        """TEST_CONSTANTS has 'instance_id_3' key."""
        assert 'instance_id_3' in TEST_CONSTANTS

    def test_has_ami_id_key(self):
        """TEST_CONSTANTS has 'ami_id' key."""
        assert 'ami_id' in TEST_CONSTANTS

    def test_has_ami_id_2_key(self):
        """TEST_CONSTANTS has 'ami_id_2' key."""
        assert 'ami_id_2' in TEST_CONSTANTS

    def test_has_ecr_digest_key(self):
        """TEST_CONSTANTS has 'ecr_digest' key."""
        assert 'ecr_digest' in TEST_CONSTANTS

    def test_has_ecr_digest_2_key(self):
        """TEST_CONSTANTS has 'ecr_digest_2' key."""
        assert 'ecr_digest_2' in TEST_CONSTANTS

    def test_has_task_arn_key(self):
        """TEST_CONSTANTS has 'task_arn' key."""
        assert 'task_arn' in TEST_CONSTANTS

    def test_has_task_arn_full_key(self):
        """TEST_CONSTANTS has 'task_arn_full' key."""
        assert 'task_arn_full' in TEST_CONSTANTS

    def test_has_test_timestamp_key(self):
        """TEST_CONSTANTS has 'test_timestamp' key."""
        assert 'test_timestamp' in TEST_CONSTANTS

    def test_has_aws_account_id_key(self):
        """TEST_CONSTANTS has 'aws_account_id' key."""
        assert 'aws_account_id' in TEST_CONSTANTS

    def test_has_aws_region_key(self):
        """TEST_CONSTANTS has 'aws_region' key."""
        assert 'aws_region' in TEST_CONSTANTS

    def test_queue_url_contains_sqs(self):
        """TEST_CONSTANTS queue_url contains 'sqs'."""
        assert 'sqs' in TEST_CONSTANTS['queue_url']

    def test_queue_url_contains_region(self):
        """TEST_CONSTANTS queue_url contains AWS region."""
        assert TEST_AWS_REGION in TEST_CONSTANTS['queue_url']

    def test_dynamodb_table_is_test_table(self):
        """TEST_CONSTANTS dynamodb_table is 'test-table'."""
        assert TEST_CONSTANTS['dynamodb_table'] == 'test-table'

    def test_lambda_function_is_test_function(self):
        """TEST_CONSTANTS lambda_function is 'test-function'."""
        assert TEST_CONSTANTS['lambda_function'] == 'test-function'

    def test_instance_id_starts_with_i(self):
        """TEST_CONSTANTS instance_id starts with 'i-'."""
        assert TEST_CONSTANTS['instance_id'].startswith('i-')

    def test_ami_id_starts_with_ami(self):
        """TEST_CONSTANTS ami_id starts with 'ami-'."""
        assert TEST_CONSTANTS['ami_id'].startswith('ami-')

    def test_ecr_digest_starts_with_sha256(self):
        """TEST_CONSTANTS ecr_digest starts with 'sha256:'."""
        assert TEST_CONSTANTS['ecr_digest'].startswith('sha256:')

    def test_task_arn_full_contains_ecs(self):
        """TEST_CONSTANTS task_arn_full contains 'ecs'."""
        assert 'ecs' in TEST_CONSTANTS['task_arn_full']

    def test_aws_account_id_is_12_digits(self):
        """TEST_CONSTANTS aws_account_id is 12 digits."""
        assert len(TEST_CONSTANTS['aws_account_id']) == 12

    def test_aws_account_id_is_all_digits(self):
        """TEST_CONSTANTS aws_account_id contains only digits."""
        assert TEST_CONSTANTS['aws_account_id'].isdigit()

    def test_aws_region_matches_terraform_config(self):
        """TEST_CONSTANTS aws_region matches TEST_AWS_REGION."""
        assert TEST_CONSTANTS['aws_region'] == TEST_AWS_REGION


# === ENV_VAR_PRESETS ===


class TestEnvVarPresets:
    """Tests for ENV_VAR_PRESETS dictionary."""

    def test_has_base_key(self):
        """ENV_VAR_PRESETS has 'base' key."""
        assert 'base' in ENV_VAR_PRESETS

    def test_has_webhook_router_key(self):
        """ENV_VAR_PRESETS has 'webhook_router' key."""
        assert 'webhook_router' in ENV_VAR_PRESETS

    def test_base_has_aws_region(self):
        """ENV_VAR_PRESETS base has AWS_REGION key."""
        assert 'AWS_REGION' in ENV_VAR_PRESETS['base']

    def test_base_aws_region_matches_test_region(self):
        """ENV_VAR_PRESETS base AWS_REGION matches TEST_AWS_REGION."""
        assert ENV_VAR_PRESETS['base']['AWS_REGION'] == TEST_AWS_REGION

    def test_webhook_router_has_aws_region(self):
        """ENV_VAR_PRESETS webhook_router has AWS_REGION key."""
        assert 'AWS_REGION' in ENV_VAR_PRESETS['webhook_router']

    def test_webhook_router_has_api_key_parameter_name(self):
        """ENV_VAR_PRESETS webhook_router has API_KEY_PARAMETER_NAME key."""
        assert 'API_KEY_PARAMETER_NAME' in ENV_VAR_PRESETS['webhook_router']

    def test_webhook_router_has_webhook_secret_name(self):
        """ENV_VAR_PRESETS webhook_router has WEBHOOK_SECRET_NAME key."""
        assert 'WEBHOOK_SECRET_NAME' in ENV_VAR_PRESETS['webhook_router']

    def test_webhook_router_has_api_base_url(self):
        """ENV_VAR_PRESETS webhook_router has API_BASE_URL key."""
        assert 'API_BASE_URL' in ENV_VAR_PRESETS['webhook_router']

    def test_webhook_router_has_idempotency_table_name(self):
        """ENV_VAR_PRESETS webhook_router has IDEMPOTENCY_TABLE_NAME key."""
        assert 'IDEMPOTENCY_TABLE_NAME' in ENV_VAR_PRESETS['webhook_router']

    def test_webhook_router_has_job_queue_url(self):
        """ENV_VAR_PRESETS webhook_router has JOB_QUEUE_URL key."""
        assert 'JOB_QUEUE_URL' in ENV_VAR_PRESETS['webhook_router']

    def test_webhook_router_api_base_url_is_https(self):
        """ENV_VAR_PRESETS webhook_router API_BASE_URL starts with https."""
        assert ENV_VAR_PRESETS['webhook_router']['API_BASE_URL'].startswith('https://')

    def test_webhook_router_job_queue_url_contains_sqs(self):
        """ENV_VAR_PRESETS webhook_router JOB_QUEUE_URL contains 'sqs'."""
        assert 'sqs' in ENV_VAR_PRESETS['webhook_router']['JOB_QUEUE_URL']

    def test_webhook_router_job_queue_url_contains_region(self):
        """ENV_VAR_PRESETS webhook_router JOB_QUEUE_URL contains region."""
        assert TEST_AWS_REGION in ENV_VAR_PRESETS['webhook_router']['JOB_QUEUE_URL']


# === load_handler_module ===


class TestLoadHandlerModule:
    """Tests for load_handler_module function."""

    def test_returns_module_type(self):
        """load_handler_module returns a ModuleType."""
        module = load_handler_module(
            "endpoints/contact_submissions/lambda/handler.py",
            "test_handler_module"
        )
        assert isinstance(module, ModuleType)

    def test_loaded_module_has_name(self):
        """load_handler_module loaded module has __name__ attribute."""
        module = load_handler_module(
            "endpoints/contact_submissions/lambda/handler.py",
            "test_handler_named"
        )
        assert hasattr(module, '__name__')

    def test_loaded_module_name_matches(self):
        """load_handler_module loaded module has correct name."""
        module = load_handler_module(
            "endpoints/contact_submissions/lambda/handler.py",
            "custom_module_name"
        )
        assert module.__name__ == "custom_module_name"

    def test_loaded_module_has_expected_function(self):
        """load_handler_module loaded module has expected function."""
        module = load_handler_module(
            "endpoints/contact_submissions/lambda/handler.py",
            "test_handler_func"
        )
        assert hasattr(module, 'get_header_case_insensitive')

    def test_loaded_function_is_callable(self):
        """load_handler_module loaded function is callable."""
        module = load_handler_module(
            "endpoints/contact_submissions/lambda/handler.py",
            "test_handler_callable"
        )
        assert callable(module.get_header_case_insensitive)


# === parse_lambda_response_payload ===


class TestParseLambdaResponsePayload:
    """Tests for parse_lambda_response_payload function."""

    def test_parses_dict_payload(self):
        """parse_lambda_response_payload parses dict payload."""
        payload_content = json.dumps({"key": "value"})
        response = {"Payload": io.BytesIO(payload_content.encode())}
        result = parse_lambda_response_payload(response)
        assert result == {"key": "value"}

    def test_parses_nested_dict_payload(self):
        """parse_lambda_response_payload parses nested dict payload."""
        payload_content = json.dumps({"outer": {"inner": "value"}})
        response = {"Payload": io.BytesIO(payload_content.encode())}
        result = parse_lambda_response_payload(response)
        assert result == {"outer": {"inner": "value"}}

    def test_parses_list_payload(self):
        """parse_lambda_response_payload parses list payload."""
        payload_content = json.dumps([1, 2, 3])
        response = {"Payload": io.BytesIO(payload_content.encode())}
        result = parse_lambda_response_payload(response)
        assert result == [1, 2, 3]

    def test_parses_string_payload(self):
        """parse_lambda_response_payload parses string payload."""
        payload_content = json.dumps("hello")
        response = {"Payload": io.BytesIO(payload_content.encode())}
        result = parse_lambda_response_payload(response)
        assert result == "hello"

    def test_parses_number_payload(self):
        """parse_lambda_response_payload parses number payload."""
        payload_content = json.dumps(42)
        response = {"Payload": io.BytesIO(payload_content.encode())}
        result = parse_lambda_response_payload(response)
        assert result == 42

    def test_parses_null_payload(self):
        """parse_lambda_response_payload parses null payload."""
        payload_content = json.dumps(None)
        response = {"Payload": io.BytesIO(payload_content.encode())}
        result = parse_lambda_response_payload(response)
        assert result is None

    def test_parses_boolean_payload(self):
        """parse_lambda_response_payload parses boolean payload."""
        payload_content = json.dumps(True)
        response = {"Payload": io.BytesIO(payload_content.encode())}
        result = parse_lambda_response_payload(response)
        assert result is True

    def test_parses_empty_dict_payload(self):
        """parse_lambda_response_payload parses empty dict payload."""
        payload_content = json.dumps({})
        response = {"Payload": io.BytesIO(payload_content.encode())}
        result = parse_lambda_response_payload(response)
        assert result == {}

    def test_parses_empty_list_payload(self):
        """parse_lambda_response_payload parses empty list payload."""
        payload_content = json.dumps([])
        response = {"Payload": io.BytesIO(payload_content.encode())}
        result = parse_lambda_response_payload(response)
        assert result == []


# === create_mock_dynamodb_client ===


class TestCreateMockDynamodbClient:
    """Tests for create_mock_dynamodb_client function."""

    def test_returns_magicmock(self):
        """create_mock_dynamodb_client returns a MagicMock."""
        mock = create_mock_dynamodb_client("get_item")
        assert isinstance(mock, MagicMock)

    def test_method_returns_default_empty_dict(self):
        """create_mock_dynamodb_client method returns empty dict by default."""
        mock = create_mock_dynamodb_client("get_item")
        result = mock.get_item()
        assert result == {}

    def test_method_returns_custom_value(self):
        """create_mock_dynamodb_client method returns custom value."""
        custom_value = {"Item": {"pk": "test"}}
        mock = create_mock_dynamodb_client("get_item", custom_value)
        result = mock.get_item()
        assert result == custom_value

    def test_batch_write_item_method(self):
        """create_mock_dynamodb_client works with batch_write_item."""
        mock = create_mock_dynamodb_client("batch_write_item")
        result = mock.batch_write_item()
        assert result == {}

    def test_put_item_method(self):
        """create_mock_dynamodb_client works with put_item."""
        mock = create_mock_dynamodb_client("put_item", {"success": True})
        result = mock.put_item()
        assert result == {"success": True}

    def test_query_method(self):
        """create_mock_dynamodb_client works with query."""
        items = {"Items": [{"id": "1"}, {"id": "2"}]}
        mock = create_mock_dynamodb_client("query", items)
        result = mock.query()
        assert result == items

    def test_scan_method(self):
        """create_mock_dynamodb_client works with scan."""
        items = {"Items": [], "Count": 0}
        mock = create_mock_dynamodb_client("scan", items)
        result = mock.scan()
        assert result == items

    def test_delete_item_method(self):
        """create_mock_dynamodb_client works with delete_item."""
        mock = create_mock_dynamodb_client("delete_item")
        result = mock.delete_item()
        assert result == {}

    def test_update_item_method(self):
        """create_mock_dynamodb_client works with update_item."""
        updated = {"Attributes": {"status": "updated"}}
        mock = create_mock_dynamodb_client("update_item", updated)
        result = mock.update_item()
        assert result == updated

    def test_returns_none_explicit(self):
        """create_mock_dynamodb_client returns empty dict when None passed."""
        mock = create_mock_dynamodb_client("get_item", None)
        result = mock.get_item()
        assert result == {}


# === assert_no_hardcoded_env_defaults ===


@pytest.fixture
def lambda_file_factory():
    """Create a temporary lambda file with given content."""
    def _create(content: str) -> Path:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as f:
            f.write(content)
            f.flush()
            return Path(f.name)
    return _create


class TestAssertNoHardcodedEnvDefaults:
    """Tests for assert_no_hardcoded_env_defaults function."""

    def test_passes_for_file_without_hardcoded_defaults(self, lambda_file_factory):
        """assert_no_hardcoded_env_defaults passes without hardcoded defaults."""
        content = """
import os
value = os.environ.get('MY_VAR')
other = os.environ['OTHER_VAR']
"""
        path = lambda_file_factory(content)
        assert assert_no_hardcoded_env_defaults(path) is None

    def test_passes_for_empty_file(self, lambda_file_factory):
        """assert_no_hardcoded_env_defaults passes for empty file."""
        path = lambda_file_factory("")
        assert assert_no_hardcoded_env_defaults(path) is None

    def test_passes_for_no_environ_usage(self, lambda_file_factory):
        """assert_no_hardcoded_env_defaults passes with no environ usage."""
        content = """
def handler(event, context):
    return {'statusCode': 200}
"""
        path = lambda_file_factory(content)
        assert assert_no_hardcoded_env_defaults(path) is None

    def test_fails_for_single_quoted_default(self, lambda_file_factory):
        """assert_no_hardcoded_env_defaults fails for single-quoted default."""
        content = "value = os.environ.get('MY_VAR', 'default')"
        path = lambda_file_factory(content)
        with pytest.raises(AssertionError):
            assert_no_hardcoded_env_defaults(path)

    def test_fails_for_double_quoted_default(self, lambda_file_factory):
        """assert_no_hardcoded_env_defaults fails for double-quoted default."""
        content = 'value = os.environ.get("MY_VAR", "default")'
        path = lambda_file_factory(content)
        with pytest.raises(AssertionError):
            assert_no_hardcoded_env_defaults(path)

    def test_fails_for_multiple_hardcoded_defaults(self, lambda_file_factory):
        """assert_no_hardcoded_env_defaults fails for multiple defaults."""
        content = """
var1 = os.environ.get('VAR1', 'default1')
var2 = os.environ.get('VAR2', 'default2')
"""
        path = lambda_file_factory(content)
        with pytest.raises(AssertionError):
            assert_no_hardcoded_env_defaults(path)

    def test_passes_for_none_default(self, lambda_file_factory):
        """assert_no_hardcoded_env_defaults passes for None default."""
        content = "value = os.environ.get('MY_VAR', None)"
        path = lambda_file_factory(content)
        assert assert_no_hardcoded_env_defaults(path) is None

    def test_passes_for_integer_default(self, lambda_file_factory):
        """assert_no_hardcoded_env_defaults passes for integer default."""
        content = "value = os.environ.get('MY_VAR', 0)"
        path = lambda_file_factory(content)
        assert assert_no_hardcoded_env_defaults(path) is None


# === Fixture Tests ===


class TestMockSqsFixture:
    """Tests for mock_sqs fixture."""

    def test_mock_sqs_is_magicmock(self, mock_sqs):
        """mock_sqs fixture provides a MagicMock."""
        assert isinstance(mock_sqs, MagicMock)

    def test_mock_sqs_has_send_message(self, mock_sqs):
        """mock_sqs fixture has send_message method."""
        assert hasattr(mock_sqs, 'send_message')

    def test_mock_sqs_send_message_is_callable(self, mock_sqs):
        """mock_sqs fixture send_message is callable."""
        assert callable(mock_sqs.send_message)

    def test_mock_sqs_has_receive_message(self, mock_sqs):
        """mock_sqs fixture has receive_message method."""
        assert hasattr(mock_sqs, 'receive_message')


class TestMockDynamodbFixture:
    """Tests for mock_dynamodb fixture."""

    def test_mock_dynamodb_is_magicmock(self, mock_dynamodb):
        """mock_dynamodb fixture provides a MagicMock."""
        assert isinstance(mock_dynamodb, MagicMock)

    def test_mock_dynamodb_has_get_item(self, mock_dynamodb):
        """mock_dynamodb fixture has get_item method."""
        assert hasattr(mock_dynamodb, 'get_item')

    def test_mock_dynamodb_get_item_is_callable(self, mock_dynamodb):
        """mock_dynamodb fixture get_item is callable."""
        assert callable(mock_dynamodb.get_item)

    def test_mock_dynamodb_has_put_item(self, mock_dynamodb):
        """mock_dynamodb fixture has put_item method."""
        assert hasattr(mock_dynamodb, 'put_item')


class TestMockSsmFixture:
    """Tests for mock_ssm fixture."""

    def test_mock_ssm_is_magicmock(self, mock_ssm):
        """mock_ssm fixture provides a MagicMock."""
        assert isinstance(mock_ssm, MagicMock)

    def test_mock_ssm_has_get_parameter(self, mock_ssm):
        """mock_ssm fixture has get_parameter method."""
        assert hasattr(mock_ssm, 'get_parameter')

    def test_mock_ssm_get_parameter_is_callable(self, mock_ssm):
        """mock_ssm fixture get_parameter is callable."""
        assert callable(mock_ssm.get_parameter)

    def test_mock_ssm_get_parameter_returns_test_token(self, mock_ssm):
        """mock_ssm fixture get_parameter returns test token."""
        result = mock_ssm.get_parameter()
        assert result['Parameter']['Value'] == 'test-token'


class TestMockCloudwatchFixture:
    """Tests for mock_cloudwatch fixture."""

    def test_mock_cloudwatch_is_magicmock(self, mock_cloudwatch):
        """mock_cloudwatch fixture provides a MagicMock."""
        assert isinstance(mock_cloudwatch, MagicMock)

    def test_mock_cloudwatch_has_put_metric_data(self, mock_cloudwatch):
        """mock_cloudwatch fixture has put_metric_data method."""
        assert hasattr(mock_cloudwatch, 'put_metric_data')

    def test_mock_cloudwatch_put_metric_data_is_callable(self, mock_cloudwatch):
        """mock_cloudwatch fixture put_metric_data is callable."""
        assert callable(mock_cloudwatch.put_metric_data)


class TestWorkflowJobEventFactoryFixture:
    """Tests for workflow_job_event_factory fixture."""

    def test_factory_is_callable(self, workflow_job_event_factory):
        """workflow_job_event_factory fixture is callable."""
        assert callable(workflow_job_event_factory)

    def test_factory_returns_dict(self, workflow_job_event_factory):
        """workflow_job_event_factory creates dict."""
        result = workflow_job_event_factory()
        assert isinstance(result, dict)

    def test_factory_result_has_path(self, workflow_job_event_factory):
        """workflow_job_event_factory result has path."""
        result = workflow_job_event_factory()
        assert 'path' in result

    def test_factory_result_has_body(self, workflow_job_event_factory):
        """workflow_job_event_factory result has body."""
        result = workflow_job_event_factory()
        assert 'body' in result


class TestSqsEventFactoryFixture:
    """Tests for sqs_event_factory fixture."""

    def test_factory_is_callable(self, sqs_event_factory):
        """sqs_event_factory fixture is callable."""
        assert callable(sqs_event_factory)

    def test_factory_returns_dict(self, sqs_event_factory):
        """sqs_event_factory creates dict."""
        result = sqs_event_factory()
        assert isinstance(result, dict)

    def test_factory_result_has_records(self, sqs_event_factory):
        """sqs_event_factory result has Records."""
        result = sqs_event_factory()
        assert 'Records' in result


class TestDlqMessageFactoryFixture:
    """Tests for dlq_message_factory fixture."""

    def test_factory_is_callable(self, dlq_message_factory):
        """dlq_message_factory fixture is callable."""
        assert callable(dlq_message_factory)

    def test_factory_returns_dict(self, dlq_message_factory):
        """dlq_message_factory creates dict."""
        result = dlq_message_factory()
        assert isinstance(result, dict)

    def test_factory_result_has_message_id(self, dlq_message_factory):
        """dlq_message_factory result has MessageId."""
        result = dlq_message_factory()
        assert 'MessageId' in result


class TestCircuitBreakerClosedStateFixture:
    """Tests for circuit_breaker_closed_state fixture."""

    def test_returns_dict(self, circuit_breaker_closed_state):
        """circuit_breaker_closed_state fixture returns dict."""
        assert isinstance(circuit_breaker_closed_state, dict)

    def test_state_is_closed(self, circuit_breaker_closed_state):
        """circuit_breaker_closed_state has 'closed' state."""
        assert circuit_breaker_closed_state['state'] == 'closed'

    def test_failure_count_is_zero(self, circuit_breaker_closed_state):
        """circuit_breaker_closed_state has zero failure_count."""
        assert circuit_breaker_closed_state['failure_count'] == 0


class TestCircuitBreakerOpenStateFixture:
    """Tests for circuit_breaker_open_state fixture."""

    def test_returns_dict(self, circuit_breaker_open_state):
        """circuit_breaker_open_state fixture returns dict."""
        assert isinstance(circuit_breaker_open_state, dict)

    def test_state_is_open(self, circuit_breaker_open_state):
        """circuit_breaker_open_state has 'open' state."""
        assert circuit_breaker_open_state['state'] == 'open'

    def test_failure_count_is_five(self, circuit_breaker_open_state):
        """circuit_breaker_open_state has five failure_count."""
        assert circuit_breaker_open_state['failure_count'] == 5


class TestMockUrllibResponseFactoryFixture:
    """Tests for mock_urllib_response_factory fixture."""

    def test_factory_is_callable(self, mock_urllib_response_factory):
        """mock_urllib_response_factory fixture is callable."""
        assert callable(mock_urllib_response_factory)

    def test_factory_creates_response_with_status(self, mock_urllib_response_factory):
        """mock_urllib_response_factory creates response with status."""
        response = mock_urllib_response_factory(status=200)
        assert response.status == 200

    def test_factory_creates_response_with_body(self, mock_urllib_response_factory):
        """mock_urllib_response_factory creates readable body."""
        response = mock_urllib_response_factory(json_data={"key": "value"})
        body = response.read().decode()
        assert body == '{"key": "value"}'

    def test_factory_creates_response_with_read_value(self, mock_urllib_response_factory):
        """mock_urllib_response_factory creates response with raw bytes."""
        response = mock_urllib_response_factory(read_value=b'raw bytes')
        body = response.read()
        assert body == b'raw bytes'

    def test_factory_response_is_context_manager(self, mock_urllib_response_factory):
        """mock_urllib_response_factory creates context manager response."""
        response = mock_urllib_response_factory()
        with response as ctx:
            assert ctx is response
