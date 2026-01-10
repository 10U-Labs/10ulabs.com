"""Unit tests for cloudwatch module."""
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from .conftest import load_lambda_module


@pytest.fixture(name="cloudwatch_module")
def cloudwatch_module_fixture():
    """Load cloudwatch module for testing."""
    with patch('boto3.client') as mock_boto_client:
        mock_boto_client.return_value = MagicMock()
        module = load_lambda_module("common/cloudwatch.py", "cloudwatch")
        # Clear the cache to ensure fresh state for each test
        module._cache = {"cloudwatch_client": None}
        yield module


class TestGetCloudwatchClient:
    """Tests for _get_cloudwatch_client function."""

    def test_creates_client_on_first_call(self, cloudwatch_module):
        """Test that client is created on first call."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            result = cloudwatch_module._get_cloudwatch_client()
            mock_boto.assert_called_once_with("cloudwatch")
            assert result == mock_client

    def test_returns_cached_client_on_second_call(self, cloudwatch_module):
        """Test that cached client is returned on subsequent calls."""
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            first_call = cloudwatch_module._get_cloudwatch_client()
            second_call = cloudwatch_module._get_cloudwatch_client()
            assert mock_boto.call_count == 1
            assert first_call is second_call


class TestPublishMetric:
    """Tests for publish_metric function."""

    def test_publishes_metric_successfully(self, cloudwatch_module):
        """Test that metric is published successfully."""
        mock_client = MagicMock()
        with patch.object(cloudwatch_module, '_get_cloudwatch_client', return_value=mock_client):
            cloudwatch_module.publish_metric("TestNamespace", "TestMetric", 1.0, "Count")
            mock_client.put_metric_data.assert_called_once()
            call_args = mock_client.put_metric_data.call_args
            assert call_args.kwargs["Namespace"] == "TestNamespace"
            assert call_args.kwargs["MetricData"][0]["MetricName"] == "TestMetric"
            assert call_args.kwargs["MetricData"][0]["Value"] == 1.0
            assert call_args.kwargs["MetricData"][0]["Unit"] == "Count"

    def test_uses_default_unit_when_not_specified(self, cloudwatch_module):
        """Test that default unit 'None' is used when not specified."""
        mock_client = MagicMock()
        with patch.object(cloudwatch_module, '_get_cloudwatch_client', return_value=mock_client):
            cloudwatch_module.publish_metric("TestNamespace", "TestMetric", 1.0)
            call_args = mock_client.put_metric_data.call_args
            assert call_args.kwargs["MetricData"][0]["Unit"] == "None"

    def test_includes_timestamp_in_metric(self, cloudwatch_module):
        """Test that timestamp is included in metric data."""
        mock_client = MagicMock()
        with patch.object(cloudwatch_module, '_get_cloudwatch_client', return_value=mock_client):
            cloudwatch_module.publish_metric("TestNamespace", "TestMetric", 1.0)
            call_args = mock_client.put_metric_data.call_args
            assert "Timestamp" in call_args.kwargs["MetricData"][0]

    def test_handles_client_error_gracefully(self, cloudwatch_module):
        """Test that ClientError is handled without raising."""
        mock_client = MagicMock()
        error = ClientError({"Error": {"Code": "500", "Message": "Error"}}, "PutMetricData")
        mock_client.put_metric_data.side_effect = error

        with patch.object(cloudwatch_module, '_get_cloudwatch_client', return_value=mock_client):
            # Should not raise, just log warning
            cloudwatch_module.publish_metric("TestNamespace", "TestMetric", 1.0)
            assert mock_client.put_metric_data.call_count == 1
