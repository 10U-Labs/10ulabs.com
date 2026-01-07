"""Unit tests for pytest_layers module."""
from unittest.mock import MagicMock

import pytest

import pytest_layers


@pytest.fixture
def mock_config():
    """Create a mock config object."""
    return MagicMock()


def _create_mock_test_context(layer_id, passed=True):
    """Create mock objects for testing pytest_runtest_makereport."""
    mock_item = MagicMock()
    mock_marker = MagicMock()
    mock_marker.args = (layer_id,)
    mock_item.iter_markers.return_value = [mock_marker]
    mock_call = MagicMock()
    mock_result = MagicMock()
    mock_result.when = 'call'
    mock_result.passed = passed
    mock_result.failed = not passed
    mock_outcome = MagicMock()
    mock_outcome.get_result.return_value = mock_result
    return mock_item, mock_call, mock_outcome


def _run_makereport(mock_item, mock_call, mock_outcome):
    """Execute the pytest_runtest_makereport generator."""
    gen = pytest_layers.pytest_runtest_makereport(mock_item, mock_call)
    next(gen)
    try:
        gen.send(mock_outcome)
    except StopIteration:
        pass


class TestPytestConfigure:
    """Tests for pytest_configure function."""

    def test_registers_layer_marker(self, mock_config):
        """Test that pytest_configure registers the layer marker."""
        pytest_layers.pytest_configure(mock_config)
        assert mock_config.addinivalue_line.call_count == 1

    def test_registered_marker_contains_layer(self, mock_config):
        """Test that the registered marker contains 'layer'."""
        pytest_layers.pytest_configure(mock_config)
        call_args = mock_config.addinivalue_line.call_args[0]
        assert 'layer' in call_args[1]

    def test_registered_marker_is_for_markers(self, mock_config):
        """Test that the marker is registered in markers section."""
        pytest_layers.pytest_configure(mock_config)
        call_args = mock_config.addinivalue_line.call_args[0]
        assert call_args[0] == 'markers'


class TestPytestRuntestMakereport:
    """Tests for pytest_runtest_makereport hook."""

    def test_tracks_passed_tests_for_layer(self):
        """Test that passed tests are tracked for the layer."""
        pytest_layers._layer_results.clear()
        mock_item, mock_call, mock_outcome = _create_mock_test_context(1, passed=True)
        _run_makereport(mock_item, mock_call, mock_outcome)
        assert pytest_layers._layer_results[1]['passed'] == 1

    def test_tracks_failed_tests_for_layer(self):
        """Test that failed tests are tracked for the layer."""
        pytest_layers._layer_results.clear()
        mock_item, mock_call, mock_outcome = _create_mock_test_context(2, passed=False)
        _run_makereport(mock_item, mock_call, mock_outcome)
        assert pytest_layers._layer_results[2]['failed'] == 1

    def test_ignores_non_call_results(self):
        """Test that setup/teardown results are ignored."""
        pytest_layers._layer_results.clear()
        mock_item = MagicMock()
        mock_marker = MagicMock()
        mock_marker.args = (3,)
        mock_item.iter_markers.return_value = [mock_marker]
        mock_call = MagicMock()
        mock_result = MagicMock()
        mock_result.when = 'setup'
        mock_result.passed = True
        mock_outcome = MagicMock()
        mock_outcome.get_result.return_value = mock_result

        _run_makereport(mock_item, mock_call, mock_outcome)
        assert 3 not in pytest_layers._layer_results

    def test_initializes_layer_in_results(self):
        """Test that layer is added to results when first test runs."""
        pytest_layers._layer_results.clear()
        mock_item, mock_call, mock_outcome = _create_mock_test_context(4, passed=True)
        _run_makereport(mock_item, mock_call, mock_outcome)
        assert 4 in pytest_layers._layer_results

    def test_initializes_passed_counter(self):
        """Test that passed counter is initialized in layer results."""
        pytest_layers._layer_results.clear()
        mock_item, mock_call, mock_outcome = _create_mock_test_context(6, passed=True)
        _run_makereport(mock_item, mock_call, mock_outcome)
        assert 'passed' in pytest_layers._layer_results[6]

    def test_initializes_failed_counter(self):
        """Test that failed counter is initialized in layer results."""
        pytest_layers._layer_results.clear()
        mock_item, mock_call, mock_outcome = _create_mock_test_context(7, passed=True)
        _run_makereport(mock_item, mock_call, mock_outcome)
        assert 'failed' in pytest_layers._layer_results[7]

    def test_handles_tests_without_layer_marker(self):
        """Test that tests without layer marker are handled gracefully."""
        pytest_layers._layer_results.clear()
        mock_item = MagicMock()
        mock_item.iter_markers.return_value = []
        mock_call = MagicMock()
        mock_result = MagicMock()
        mock_result.when = 'call'
        mock_result.passed = True
        mock_outcome = MagicMock()
        mock_outcome.get_result.return_value = mock_result

        _run_makereport(mock_item, mock_call, mock_outcome)
        assert len(pytest_layers._layer_results) == 0


class TestPytestRuntestSetup:
    """Tests for pytest_runtest_setup hook."""

    def test_does_not_raise(self):
        """Test that pytest_runtest_setup does not raise."""
        mock_item = MagicMock()
        pytest_layers.pytest_runtest_setup(mock_item)
        assert True

    def test_returns_none(self):
        """Test that pytest_runtest_setup returns None."""
        mock_item = MagicMock()
        result = pytest_layers.pytest_runtest_setup(mock_item)
        assert result is None


class TestLayerResultsTracking:
    """Tests for _layer_results global state."""

    def test_layer_results_is_dict(self):
        """Test that _layer_results is a dictionary."""
        assert isinstance(pytest_layers._layer_results, dict)

    def test_multiple_tests_accumulate(self):
        """Test that multiple tests in same layer accumulate counts."""
        pytest_layers._layer_results.clear()
        mock_item, mock_call, mock_outcome = _create_mock_test_context(5, passed=True)

        for _ in range(3):
            _run_makereport(mock_item, mock_call, mock_outcome)

        assert pytest_layers._layer_results[5]['passed'] == 3
