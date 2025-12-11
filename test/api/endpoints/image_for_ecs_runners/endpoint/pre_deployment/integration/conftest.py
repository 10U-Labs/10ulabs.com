"""Fixtures for image_for_ecs_runners endpoint pre-deployment integration tests."""
from test.api.endpoints.image_for_ecs_runners.conftest import get_ecr_repository

import pytest


@pytest.fixture(scope="session")
def ecr_repository_name():
    """Provide the ECR repository name."""
    return get_ecr_repository()
