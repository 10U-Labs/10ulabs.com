"""Unit tests for circuit breaker reset API.

Five-layer model: Existence, Configuration, Capability.
"""
import os
from contextlib import contextmanager
from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError

from boto_mocks import (
    create_mock_lambda_list_mappings_error,
    create_mock_lambda_with_disabled_mappings,
)
from lambda_response import parse_response_body, assert_response_status
from .conftest import circuit_breaker_utils


CB_ENV = {'WEBHOOK_FUNCTION_NAME': 'test-function', 'STATE_TABLE_NAME': 'test-table'}
CB_PATH = '/v1/webhooks/github/jit-runner-requests/circuit-breaker'
CB_RESET_PATH = f'{CB_PATH}/reset'


@contextmanager
def _patched_cb_handler(mock_dynamodb, mock_lambda):
    """Context manager for patching circuit breaker handler dependencies."""
    with patch.dict(os.environ, CB_ENV):
        with patch('boto3.client') as mock_boto_client:
            mock_boto_client.side_effect = lambda svc: (
                mock_dynamodb if svc == 'dynamodb' else mock_lambda
            )
            yield


def _invoke_handler(circuit_breaker_reset, event, context, mock_dynamodb, mock_lambda):
    """Invoke handler with patched dependencies."""
    with _patched_cb_handler(mock_dynamodb, mock_lambda):
        return circuit_breaker_reset.lambda_handler(event, context)


def _create_post_reset_mocks():
    """Create mock clients for POST reset handler tests."""
    mock_lambda = MagicMock()
    mock_lambda.list_event_source_mappings.return_value = {'EventSourceMappings': []}
    mock_dynamodb = MagicMock()
    return mock_dynamodb, mock_lambda


class TestGetCircuitBreakerStatus:
    """Tests for get_circuit_breaker_status function."""

    def test_01_gets_dynamodb_state(self, circuit_breaker_reset, cb_status_mock_factory):
        """Test get circuit breaker status fetches DynamoDB state."""
        mock_dynamodb, mock_lambda = cb_status_mock_factory()
        with patch('boto3.client') as mock_boto_client:
            mock_boto_client.side_effect = lambda svc: (
                mock_dynamodb if svc == 'dynamodb' else mock_lambda
            )
            circuit_breaker_reset.get_circuit_breaker_status(
                'test-function', 'test-table'
            )
        assert mock_dynamodb.get_item.called

    def test_02_returns_healthy_when_closed(
        self, circuit_breaker_reset, cb_status_mock_factory
    ):
        """Test get circuit breaker status returns healthy when state is closed."""
        mock_dynamodb, mock_lambda = cb_status_mock_factory(db_state='closed')
        with patch('boto3.client') as mock_boto_client:
            mock_boto_client.side_effect = lambda svc: (
                mock_dynamodb if svc == 'dynamodb' else mock_lambda
            )
            result = circuit_breaker_reset.get_circuit_breaker_status(
                'test-function', 'test-table'
            )
        assert result['healthy'] is True

    def test_03_returns_unhealthy_when_open(
        self, circuit_breaker_reset, cb_status_mock_factory
    ):
        """Test get circuit breaker status returns unhealthy when state is open."""
        mock_dynamodb, mock_lambda = cb_status_mock_factory(
            db_state='open', sqs_state='Disabled', concurrency=0
        )
        with patch('boto3.client') as mock_boto_client:
            mock_boto_client.side_effect = lambda svc: (
                mock_dynamodb if svc == 'dynamodb' else mock_lambda
            )
            result = circuit_breaker_reset.get_circuit_breaker_status(
                'test-function', 'test-table'
            )
        assert result['healthy'] is False

    def test_04_includes_state_in_response(
        self, circuit_breaker_reset, cb_status_mock_factory
    ):
        """Test get circuit breaker status includes state in response."""
        mock_dynamodb, mock_lambda = cb_status_mock_factory(db_state='half-open')
        with patch('boto3.client') as mock_boto_client:
            mock_boto_client.side_effect = lambda svc: (
                mock_dynamodb if svc == 'dynamodb' else mock_lambda
            )
            result = circuit_breaker_reset.get_circuit_breaker_status(
                'test-function', 'test-table'
            )
        assert result['state'] == 'half-open'

    def test_05_handles_dynamodb_error(self, circuit_breaker_reset):
        """Test get circuit breaker status handles DynamoDB error gracefully."""
        with patch('boto3.client') as mock_boto_client:
            mock_dynamodb = MagicMock()
            mock_dynamodb.get_item.side_effect = ClientError(
                {'Error': {'Code': 'ServiceUnavailable'}}, 'GetItem'
            )
            mock_lambda = MagicMock()
            mock_lambda.list_event_source_mappings.return_value = {
                'EventSourceMappings': []
            }
            mock_lambda.get_function_concurrency.return_value = {}
            mock_boto_client.side_effect = lambda svc: (
                mock_dynamodb if svc == 'dynamodb' else mock_lambda
            )
            result = circuit_breaker_reset.get_circuit_breaker_status(
                'test-function', 'test-table'
            )
        assert result['state'] == 'error'


def create_sqs_mappings_mock(mappings=None):
    """Create Lambda client mock with event source mappings."""
    mock_lam = MagicMock()
    mock_lam.list_event_source_mappings.return_value = {
        'EventSourceMappings': mappings if mappings is not None else []
    }
    return mock_lam


class TestEnableEventSourceMappings:
    """Tests for enable_event_source_mappings (from common module, used by reset)."""

    def test_01_lists_event_source_mappings(self):
        """Test enable event source mappings lists mappings."""
        mock_lam = create_sqs_mappings_mock([])
        with patch.object(circuit_breaker_utils, 'get_lambda_client', return_value=mock_lam):
            circuit_breaker_utils.enable_event_source_mappings('test-function')
        assert mock_lam.list_event_source_mappings.called

    def test_02_enables_disabled_mappings(self):
        """Test enable event source mappings enables disabled mappings."""
        mock_lam = create_mock_lambda_with_disabled_mappings()
        with patch.object(circuit_breaker_utils, 'get_lambda_client', return_value=mock_lam):
            circuit_breaker_utils.enable_event_source_mappings('test-function')
        assert mock_lam.update_event_source_mapping.called

    def test_03_counts_enabled_mappings(self):
        """Test enable event source mappings counts enabled mappings."""
        mappings = [
            {'UUID': 'map-1', 'State': 'Disabled'},
            {'UUID': 'map-2', 'State': 'Disabled'}
        ]
        mock_lam = create_sqs_mappings_mock(mappings)
        with patch.object(circuit_breaker_utils, 'get_lambda_client', return_value=mock_lam):
            result = circuit_breaker_utils.enable_event_source_mappings('test-function')
        assert result['enabled_count'] == 2

    def test_04_handles_no_mappings(self):
        """Test enable event source mappings handles no mappings."""
        mock_lam = create_sqs_mappings_mock([])
        with patch.object(circuit_breaker_utils, 'get_lambda_client', return_value=mock_lam):
            result = circuit_breaker_utils.enable_event_source_mappings('test-function')
        assert result['enabled_count'] == 0

    def test_05_handles_api_error(self):
        """Test enable event source mappings handles API error."""
        mock_lam = create_mock_lambda_list_mappings_error()
        with patch.object(circuit_breaker_utils, 'get_lambda_client', return_value=mock_lam):
            result = circuit_breaker_utils.enable_event_source_mappings('test-function')
        assert result['success'] is False


class TestRemoveLambdaReservedConcurrency:
    """Tests for remove_lambda_reserved_concurrency function."""

    def test_01_deletes_concurrency(self, circuit_breaker_reset):
        """Test remove lambda reserved concurrency deletes concurrency."""
        mock_lambda = MagicMock()
        with patch.object(circuit_breaker_reset, 'get_lambda_client', return_value=mock_lambda):
            circuit_breaker_reset.remove_lambda_reserved_concurrency('test-function')
        assert mock_lambda.delete_function_concurrency.called

    def test_02_returns_success(self, circuit_breaker_reset):
        """Test remove lambda reserved concurrency returns success."""
        mock_lambda = MagicMock()
        with patch.object(circuit_breaker_reset, 'get_lambda_client', return_value=mock_lambda):
            result = circuit_breaker_reset.remove_lambda_reserved_concurrency(
                'test-function'
            )
        assert result['success'] is True

    def test_03_handles_not_found(self, circuit_breaker_reset):
        """Test remove lambda reserved concurrency handles not found."""
        mock_lambda = MagicMock()
        mock_lambda.exceptions.ResourceNotFoundException = Exception
        mock_lambda.delete_function_concurrency.side_effect = (
            mock_lambda.exceptions.ResourceNotFoundException
        )
        with patch.object(circuit_breaker_reset, 'get_lambda_client', return_value=mock_lambda):
            result = circuit_breaker_reset.remove_lambda_reserved_concurrency(
                'test-function'
            )
        assert result['success'] is True

    def test_04_handles_api_error(self, circuit_breaker_reset):
        """Test remove lambda reserved concurrency handles API error."""
        mock_lambda = MagicMock()
        mock_lambda.exceptions.ResourceNotFoundException = type(
            'ResourceNotFoundException', (Exception,), {}
        )
        mock_lambda.delete_function_concurrency.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable'}}, 'DeleteFunctionConcurrency'
        )
        with patch.object(circuit_breaker_reset, 'get_lambda_client', return_value=mock_lambda):
            result = circuit_breaker_reset.remove_lambda_reserved_concurrency(
                'test-function'
            )
        assert result['success'] is False


class TestResetCircuitBreakerState:
    """Tests for reset_circuit_breaker_state function."""

    def test_01_puts_closed_state(self, circuit_breaker_reset, cb_dynamodb_reset_mock):
        """Test reset circuit breaker state puts closed state."""
        circuit_breaker_reset.reset_circuit_breaker_state('test-table')
        put_args = cb_dynamodb_reset_mock.put_item.call_args
        assert put_args[1]['Item']['state']['S'] == 'closed'

    def test_02_resets_recovery_attempts(
        self, circuit_breaker_reset, cb_dynamodb_reset_mock
    ):
        """Test reset circuit breaker state resets recovery attempts."""
        circuit_breaker_reset.reset_circuit_breaker_state('test-table')
        put_args = cb_dynamodb_reset_mock.put_item.call_args
        assert put_args[1]['Item']['recovery_attempts']['N'] == '0'

    def test_03_returns_success(self, circuit_breaker_reset, cb_dynamodb_reset_mock):
        """Test reset circuit breaker state returns success."""
        _ = cb_dynamodb_reset_mock  # Fixture provides patched boto3.client
        result = circuit_breaker_reset.reset_circuit_breaker_state('test-table')
        assert result['success'] is True

    def test_04_handles_dynamodb_error(self, circuit_breaker_reset):
        """Test reset circuit breaker state handles DynamoDB error."""
        with patch('boto3.client') as mock_boto:
            mock_db = MagicMock()
            mock_db.put_item.side_effect = ClientError(
                {'Error': {'Code': 'ServiceUnavailable'}}, 'PutItem'
            )
            mock_boto.return_value = mock_db
            result = circuit_breaker_reset.reset_circuit_breaker_state('test-table')
        assert result['success'] is False


class TestLambdaHandlerGetStatus:
    """Tests for lambda_handler GET requests."""

    def test_01_returns_200_when_healthy(
        self, circuit_breaker_reset, lambda_context, cb_status_mock_factory
    ):
        """Test lambda handler returns 200 when circuit breaker is healthy."""
        event = {'httpMethod': 'GET', 'path': CB_PATH}
        mock_dynamodb, mock_lambda = cb_status_mock_factory(db_state='closed')
        response = _invoke_handler(
            circuit_breaker_reset, event, lambda_context, mock_dynamodb, mock_lambda
        )
        assert response['statusCode'] == 200

    def test_02_returns_503_when_unhealthy(
        self, circuit_breaker_reset, lambda_context, cb_status_mock_factory
    ):
        """Test lambda handler returns 503 when circuit breaker is unhealthy."""
        event = {'httpMethod': 'GET', 'path': CB_PATH}
        mock_dynamodb, mock_lambda = cb_status_mock_factory(
            db_state='open', sqs_state='Disabled', concurrency=0
        )
        response = _invoke_handler(
            circuit_breaker_reset, event, lambda_context, mock_dynamodb, mock_lambda
        )
        assert response['statusCode'] == 503

    def test_03_includes_cors_headers(
        self, circuit_breaker_reset, lambda_context, cb_status_mock_factory
    ):
        """Test lambda handler includes CORS headers."""
        event = {'httpMethod': 'GET', 'path': CB_PATH}
        mock_dynamodb, mock_lambda = cb_status_mock_factory(db_state='closed')
        response = _invoke_handler(
            circuit_breaker_reset, event, lambda_context, mock_dynamodb, mock_lambda
        )
        assert response['headers']['Access-Control-Allow-Origin'] == '*'


class TestLambdaHandlerPostReset:
    """Tests for lambda_handler POST reset requests."""

    def test_01_returns_200_on_successful_reset(
        self, circuit_breaker_reset, lambda_context
    ):
        """Test lambda handler returns 200 on successful reset."""
        event = {'httpMethod': 'POST', 'path': CB_RESET_PATH}
        mock_dynamodb, mock_lambda = _create_post_reset_mocks()
        response = _invoke_handler(
            circuit_breaker_reset, event, lambda_context, mock_dynamodb, mock_lambda
        )
        assert response['statusCode'] == 200

    def test_02_returns_success_true(self, circuit_breaker_reset, lambda_context):
        """Test lambda handler returns success true on reset."""
        event = {'httpMethod': 'POST', 'path': CB_RESET_PATH}
        mock_dynamodb, mock_lambda = _create_post_reset_mocks()
        response = _invoke_handler(
            circuit_breaker_reset, event, lambda_context, mock_dynamodb, mock_lambda
        )
        body = parse_response_body(response)
        assert body['success'] is True

    def test_03_includes_details(self, circuit_breaker_reset, lambda_context):
        """Test lambda handler includes details in reset response."""
        event = {'httpMethod': 'POST', 'path': CB_RESET_PATH}
        mock_dynamodb, mock_lambda = _create_post_reset_mocks()
        response = _invoke_handler(
            circuit_breaker_reset, event, lambda_context, mock_dynamodb, mock_lambda
        )
        body = parse_response_body(response)
        assert 'details' in body

    def test_04_returns_500_on_partial_failure(
        self, circuit_breaker_reset, lambda_context
    ):
        """Test lambda handler returns 500 on partial failure."""
        event = {'httpMethod': 'POST', 'path': CB_RESET_PATH}
        mock_dynamodb = MagicMock()
        mock_lambda = MagicMock()
        mock_lambda.list_event_source_mappings.side_effect = ClientError(
            {'Error': {'Code': 'ServiceUnavailable'}}, 'ListEventSourceMappings'
        )
        response = _invoke_handler(
            circuit_breaker_reset, event, lambda_context, mock_dynamodb, mock_lambda
        )
        assert response['statusCode'] == 500


class TestLambdaHandlerPostDirectPath:
    """Tests for POST on CB_PATH directly (without /reset suffix)."""

    def test_01_accepts_post_on_circuit_breaker_path(
        self, circuit_breaker_reset, lambda_context
    ):
        """Test POST works on CB_PATH directly."""
        event = {'httpMethod': 'POST', 'path': CB_PATH}
        mock_dynamodb, mock_lambda = _create_post_reset_mocks()
        response = _invoke_handler(
            circuit_breaker_reset, event, lambda_context, mock_dynamodb, mock_lambda
        )
        assert response['statusCode'] == 200

    def test_02_returns_success_on_direct_path(
        self, circuit_breaker_reset, lambda_context
    ):
        """Test POST on /circuit-breaker returns success."""
        event = {'httpMethod': 'POST', 'path': CB_PATH}
        mock_dynamodb, mock_lambda = _create_post_reset_mocks()
        response = _invoke_handler(
            circuit_breaker_reset, event, lambda_context, mock_dynamodb, mock_lambda
        )
        body = parse_response_body(response)
        assert body['success'] is True

    def test_03_includes_details_on_direct_path(
        self, circuit_breaker_reset, lambda_context
    ):
        """Test POST on /circuit-breaker includes details."""
        event = {'httpMethod': 'POST', 'path': CB_PATH}
        mock_dynamodb, mock_lambda = _create_post_reset_mocks()
        response = _invoke_handler(
            circuit_breaker_reset, event, lambda_context, mock_dynamodb, mock_lambda
        )
        body = parse_response_body(response)
        assert 'details' in body


class TestLambdaHandlerMethodNotAllowed:
    """Tests for unsupported HTTP methods."""

    def test_01_returns_405_for_unsupported_methods(
        self, circuit_breaker_reset, lambda_context
    ):
        """Test lambda handler returns 405 for unsupported methods."""
        event = {'httpMethod': 'DELETE', 'path': CB_PATH}
        with patch.dict(os.environ, {
            'WEBHOOK_FUNCTION_NAME': 'test-function',
            'STATE_TABLE_NAME': 'test-table'
        }):
            response = circuit_breaker_reset.lambda_handler(event, lambda_context)
        assert response['statusCode'] == 405

    def test_02_includes_error_message(self, circuit_breaker_reset, lambda_context):
        """Test lambda handler includes error message for 405."""
        event = {'httpMethod': 'PUT', 'path': CB_PATH}
        with patch.dict(os.environ, {
            'WEBHOOK_FUNCTION_NAME': 'test-function',
            'STATE_TABLE_NAME': 'test-table'
        }):
            response = circuit_breaker_reset.lambda_handler(event, lambda_context)
            body = parse_response_body(response)
        assert 'error' in body
