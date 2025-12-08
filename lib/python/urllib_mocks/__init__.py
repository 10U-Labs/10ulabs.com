"""Mock utilities for urllib testing."""
import json
from typing import Any, Callable, Dict, Optional
from unittest.mock import Mock


def create_mock_urllib_response(
    read_value: bytes = b'',
    status: int = 200,
    json_data: Optional[Dict[str, Any]] = None
) -> Mock:
    """Create a mock urllib response object.

    Args:
        read_value: Raw bytes to return from read().
        status: HTTP status code.
        json_data: If provided, JSON-encode this as the response body.

    Returns:
        Mock object that behaves like a urllib response.
    """
    mock_response = Mock()
    if json_data is not None:
        mock_response.read.return_value = json.dumps(json_data).encode()
    else:
        mock_response.read.return_value = read_value
    mock_response.status = status
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)
    return mock_response


def mock_urllib_response_factory() -> Callable[..., Mock]:
    """Return a factory function for creating mock urllib responses.

    Returns:
        Factory function that creates mock urllib response objects.
    """
    return create_mock_urllib_response
