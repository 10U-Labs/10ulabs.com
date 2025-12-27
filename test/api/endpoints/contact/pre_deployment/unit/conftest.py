"""Pytest fixtures for contact handler pre-deployment unit tests."""
import json
from types import ModuleType
from unittest.mock import patch

import pytest

from module_utils import load_module_from_path
from repo_utils import REPO_ROOT

CONTACT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "contact"


def load_contact_handler_module() -> ModuleType:
    """Load the contact handler module dynamically."""
    handler_path = CONTACT_SRC / "lambda" / "handler.py"
    return load_module_from_path("contact_handler", handler_path)


@pytest.fixture
def contact_handler() -> ModuleType:
    """Load and return the contact handler module."""
    return load_contact_handler_module()


@pytest.fixture
def contact_post_event():
    """Create a sample POST event for contact endpoint testing."""
    return {
        'path': '/v1/contact',
        'httpMethod': 'POST',
        'headers': {},
        'body': json.dumps({
            'name': 'John Doe',
            'email': 'john@example.com',
            'message': 'Hello, this is a test message.',
            'recaptcha_token': 'valid-token'
        }),
        'requestContext': {'requestId': 'test-id'}
    }


@pytest.fixture
def successful_contact_response(request):
    """Return response from a successful contact form submission."""
    handler = request.getfixturevalue("contact_handler")
    event = request.getfixturevalue("contact_post_event")
    ctx = request.getfixturevalue("lambda_context")
    with patch.object(handler, "get_recaptcha_secret", return_value="secret"):
        with patch.object(handler, "verify_recaptcha", return_value=True):
            with patch.object(handler, "send_contact_email", return_value=True):
                with patch.dict("os.environ", {"CONTACT_EMAIL": "contact@test.com"}):
                    return handler.handler(event, ctx)
