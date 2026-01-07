"""Unit tests for urllib_mocks module."""
import json

from urllib_mocks import create_mock_urllib_response, mock_urllib_response_factory


class TestCreateMockUrllibResponse:
    """Tests for create_mock_urllib_response function."""

    def test_returns_mock_object(self):
        """Test that function returns a mock object."""
        result = create_mock_urllib_response()
        assert result is not None

    def test_default_status_is_200(self):
        """Test that default status is 200."""
        result = create_mock_urllib_response()
        assert result.status == 200

    def test_custom_status_code(self):
        """Test that custom status code is set."""
        result = create_mock_urllib_response(status=404)
        assert result.status == 404

    def test_default_read_returns_empty_bytes(self):
        """Test that default read returns empty bytes."""
        result = create_mock_urllib_response()
        assert result.read() == b''

    def test_custom_read_value(self):
        """Test that custom read_value is returned."""
        result = create_mock_urllib_response(read_value=b'test data')
        assert result.read() == b'test data'

    def test_json_data_is_encoded(self):
        """Test that json_data is JSON encoded."""
        result = create_mock_urllib_response(json_data={'key': 'value'})
        read_value = result.read()
        assert json.loads(read_value) == {'key': 'value'}

    def test_json_data_overrides_read_value(self):
        """Test that json_data takes precedence over read_value."""
        result = create_mock_urllib_response(
            read_value=b'ignored',
            json_data={'key': 'value'}
        )
        read_value = result.read()
        assert json.loads(read_value) == {'key': 'value'}

    def test_context_manager_enter(self):
        """Test that mock supports context manager __enter__."""
        result = create_mock_urllib_response()
        context = result.__enter__()
        assert context is result

    def test_context_manager_exit(self):
        """Test that mock supports context manager __exit__."""
        result = create_mock_urllib_response()
        exit_value = result.__exit__(None, None, None)
        assert exit_value is False

    def test_can_be_used_with_with_statement(self):
        """Test that mock can be used in with statement."""
        result = create_mock_urllib_response(json_data={'status': 'ok'})
        with result as response:
            data = json.loads(response.read())
            assert data == {'status': 'ok'}

    def test_json_data_with_list(self):
        """Test that json_data works with list."""
        result = create_mock_urllib_response(json_data=[1, 2, 3])
        read_value = result.read()
        assert json.loads(read_value) == [1, 2, 3]

    def test_json_data_with_nested_structure(self):
        """Test that json_data works with nested structures."""
        nested_data = {'users': [{'id': 1, 'name': 'test'}]}
        result = create_mock_urllib_response(json_data=nested_data)
        read_value = result.read()
        assert json.loads(read_value) == nested_data


class TestMockUrllibResponseFactory:
    """Tests for mock_urllib_response_factory function."""

    def test_returns_callable(self):
        """Test that factory returns a callable."""
        factory = mock_urllib_response_factory()
        assert callable(factory)

    def test_factory_is_create_function(self):
        """Test that factory is the create_mock_urllib_response function."""
        factory = mock_urllib_response_factory()
        assert factory is create_mock_urllib_response

    def test_factory_creates_mock_with_default_status(self):
        """Test that factory creates mock with default status."""
        factory = mock_urllib_response_factory()
        result = factory()
        assert result.status == 200

    def test_factory_creates_mock_with_custom_json(self):
        """Test that factory creates mock with custom JSON."""
        factory = mock_urllib_response_factory()
        result = factory(json_data={'test': True})
        data = json.loads(result.read())
        assert data == {'test': True}
