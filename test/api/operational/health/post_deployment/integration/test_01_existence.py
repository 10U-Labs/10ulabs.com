"""Layer 1: Existence tests for health endpoint post-deployment.

Tests ONLY that resources exist. No configuration checks.
These tests verify that resources created by THIS workflow exist after deployment.

Three-layer testing model:
- Layer 1: Existence - Resources were created
"""

import pytest

from test_fixtures.integration import create_lambda_existence_tests


pytestmark = pytest.mark.layer(1)

TestDeployedResourcesExist = create_lambda_existence_tests(
    function_name_config_key="health_handler_function_name",
    default_function_name="TenULabsHealthHandler",
    terraform_path="src/api/operational/health/",
    log_group_fixture="health_handler_log_group",
)
