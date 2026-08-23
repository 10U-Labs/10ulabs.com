"""Comprehensive tests for test_fixtures.unit module."""
from unittest.mock import MagicMock

from test_fixtures.unit import (
    TEST_CONSTANTS,
    ENV_VAR_PRESETS,
    create_mock_dynamodb_client,
)
from terraform_config import TEST_AWS_REGION


# === TEST_CONSTANTS ===


class TestTestConstantsKeys:
    """Tests that TEST_CONSTANTS carries the keys its readers ask for."""

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


class TestTestConstantsValues:
    """Tests the shape of the values TEST_CONSTANTS carries."""

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

    def test_base_has_aws_region(self):
        """ENV_VAR_PRESETS base has AWS_REGION key."""
        assert 'AWS_REGION' in ENV_VAR_PRESETS['base']

    def test_base_aws_region_matches_test_region(self):
        """ENV_VAR_PRESETS base AWS_REGION matches TEST_AWS_REGION."""
        assert ENV_VAR_PRESETS['base']['AWS_REGION'] == TEST_AWS_REGION


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
