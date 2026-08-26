import json
from typing import Any, Callable, Dict, Optional
from unittest.mock import Mock


def create_mock_urllib_response(
    read_value: bytes = b'',
    status: int = 200,
    json_data: Optional[Dict[str, Any]] = None
) -> Mock:
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
    return create_mock_urllib_response
