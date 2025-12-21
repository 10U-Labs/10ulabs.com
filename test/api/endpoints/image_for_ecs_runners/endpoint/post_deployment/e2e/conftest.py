"""Fixtures for image_for_ecs_runners endpoint E2E tests."""
import pytest

from ..conftest import create_api_request_fixture


api_request = pytest.fixture(scope="session")(create_api_request_fixture(test_mode_param=True))
