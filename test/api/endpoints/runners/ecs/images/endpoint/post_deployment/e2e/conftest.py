"""Fixtures for runners/ecs/images endpoint E2E tests."""
import pytest

from ..conftest import create_api_request_fixture


api_request = pytest.fixture(scope="session")(create_api_request_fixture(test_mode_param=True))
