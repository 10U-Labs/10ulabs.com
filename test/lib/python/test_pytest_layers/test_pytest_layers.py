"""Unit tests for pytest_layers module."""
from unittest.mock import MagicMock

import pytest_layers


class TestPytestConfigure:
    """Tests for pytest_configure function."""

    def test_registers_layer_marker(self):
        """Test that pytest_configure registers the layer marker."""
        mock_config = MagicMock()
        pytest_layers.pytest_configure(mock_config)
        mock_config.addinivalue_line.assert_called_once()

    def test_registered_marker_contains_layer(self):
        """Test that the registered marker contains 'layer'."""
        mock_config = MagicMock()
        pytest_layers.pytest_configure(mock_config)
        call_args = mock_config.addinivalue_line.call_args[0]
        assert 'layer' in call_args[1]

    def test_registered_marker_is_for_markers(self):
        """Test that the marker is registered in markers section."""
        mock_config = MagicMock()
        pytest_layers.pytest_configure(mock_config)
        call_args = mock_config.addinivalue_line.call_args[0]
        assert call_args[0] == 'markers'


class TestPytestRuntestMakereport:
    """Tests for pytest_runtest_makereport hook."""

    def test_tracks_passed_tests_for_layer(self):
        """Test that passed tests are tracked for the layer."""
        pytest_layers._layer_results.clear()
        mock_item = MagicMock()
        mock_marker = MagicMock()
        mock_marker.args = (1,)
        mock_item.iter_markers.return_value = [mock_marker]
        mock_call = MagicMock()
        mock_result = MagicMock()
        mock_result.when = 'call'
        mock_result.passed = True
        mock_result.failed = False
        mock_outcome = MagicMock()
        mock_outcome.get_result.return_value = mock_result

        gen = pytest_layers.pytest_runtest_makereport(mock_item, mock_call)
        next(gen)
        try:
            gen.send(mock_outcome)
        except StopIteration:
            pass

        assert pytest_layers._layer_results[1]['passed'] == 1

    def test_tracks_failed_tests_for_layer(self):
        """Test that failed tests are tracked for the layer."""
        pytest_layers._layer_results.clear()
        mock_item = MagicMock()
        mock_marker = MagicMock()
        mock_marker.args = (2,)
        mock_item.iter_markers.return_value = [mock_marker]
        mock_call = MagicMock()
        mock_result = MagicMock()
        mock_result.when = 'call'
        mock_result.passed = False
        mock_result.failed = True
        mock_outcome = MagicMock()
        mock_outcome.get_result.return_value = mock_result

        gen = pytest_layers.pytest_runtest_makereport(mock_item, mock_call)
        next(gen)
        try:
            gen.send(mock_outcome)
        except StopIteration:
            pass

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

        gen = pytest_layers.pytest_runtest_makereport(mock_item, mock_call)
        next(gen)
        try:
            gen.send(mock_outcome)
        except StopIteration:
            pass

        assert 3 not in pytest_layers._layer_results

    def test_initializes_layer_results_if_needed(self):
        """Test that layer results are initialized when first test runs."""
        pytest_layers._layer_results.clear()
        mock_item = MagicMock()
        mock_marker = MagicMock()
        mock_marker.args = (4,)
        mock_item.iter_markers.return_value = [mock_marker]
        mock_call = MagicMock()
        mock_result = MagicMock()
        mock_result.when = 'call'
        mock_result.passed = True
        mock_result.failed = False
        mock_outcome = MagicMock()
        mock_outcome.get_result.return_value = mock_result

        gen = pytest_layers.pytest_runtest_makereport(mock_item, mock_call)
        next(gen)
        try:
            gen.send(mock_outcome)
        except StopIteration:
            pass

        assert 4 in pytest_layers._layer_results
        assert 'passed' in pytest_layers._layer_results[4]
        assert 'failed' in pytest_layers._layer_results[4]

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

        gen = pytest_layers.pytest_runtest_makereport(mock_item, mock_call)
        next(gen)
        try:
            gen.send(mock_outcome)
        except StopIteration:
            pass

        assert len(pytest_layers._layer_results) == 0


class TestPytestRuntestSetup:
    """Tests for pytest_runtest_setup hook."""

    def test_does_not_raise(self):
        """Test that pytest_runtest_setup does not raise."""
        mock_item = MagicMock()
        pytest_layers.pytest_runtest_setup(mock_item)
        assert True

    def test_accepts_item_parameter(self):
        """Test that pytest_runtest_setup accepts an item parameter."""
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
        mock_item = MagicMock()
        mock_marker = MagicMock()
        mock_marker.args = (5,)
        mock_item.iter_markers.return_value = [mock_marker]
        mock_call = MagicMock()
        mock_result = MagicMock()
        mock_result.when = 'call'
        mock_result.passed = True
        mock_result.failed = False
        mock_outcome = MagicMock()
        mock_outcome.get_result.return_value = mock_result

        for _ in range(3):
            gen = pytest_layers.pytest_runtest_makereport(mock_item, mock_call)
            next(gen)
            try:
                gen.send(mock_outcome)
            except StopIteration:
                pass

        assert pytest_layers._layer_results[5]['passed'] == 3
