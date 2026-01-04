"""Layer 1: Existence tests for diagnostics endpoint post-deployment.

Tests ONLY that resources exist. No configuration checks.
These tests verify that resources created by THIS workflow exist after deployment.

Three-layer testing model:
- Layer 1: Existence - Resources were created
"""


from test_fixtures.integration import create_lambda_existence_tests



TestDeployedResourcesExist = create_lambda_existence_tests(
    function_name_config_key="diagnostics_handler_function_name",
    default_function_name="TenULabsDiagnosticsHandler",
    terraform_path="src/api/operational/diagnostics/",
    log_group_fixture="diagnostics_handler_log_group",
)
