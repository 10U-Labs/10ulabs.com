"""Terraform configuration tests for sessions endpoint.

Tests verify Terraform configuration correctness without deploying:
- Lambda lifecycle rules for environment variable handling
- IAM role naming conventions (PascalCase)
- Lambda function naming conventions (PascalCase)
"""
from pathlib import Path

from naming_conventions import validate_name
from repo_utils import REPO_ROOT
from test_fixtures.lambda_lifecycle import create_lambda_lifecycle_tests

SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"


# Generate Lambda lifecycle tests for all Terraform files with Lambda definitions
TestLambdaLifecycle = create_lambda_lifecycle_tests(
    endpoint_src=SESSIONS_SRC_PATH,
    tf_files=["lambda.tf", "analytics.tf"]
)


class TestIamRoleNamingConventions:
    """Tests for IAM role naming conventions."""

    def test_sessions_handler_role_name_is_pascalcase(self):
        """Verify SessionsHandlerRole follows PascalCase naming."""
        iam_tf = SESSIONS_SRC_PATH / "iam.tf"
        content = iam_tf.read_text()
        assert 'SessionsHandlerRole' in content

    def test_sessions_export_role_name_is_pascalcase(self):
        """Verify SessionsExportRole follows PascalCase naming."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'SessionsExportRole' in content

    def test_sessions_crawler_trigger_role_name_is_pascalcase(self):
        """Verify SessionsCrawlerTriggerRole follows PascalCase naming."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'SessionsCrawlerTriggerRole' in content

    def test_sessions_glue_crawler_role_name_is_pascalcase(self):
        """Verify SessionsGlueCrawlerRole follows PascalCase naming."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'SessionsGlueCrawlerRole' in content

    def test_sessions_scheduler_role_name_is_pascalcase(self):
        """Verify SessionsSchedulerRole follows PascalCase naming."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'SessionsSchedulerRole' in content


class TestLambdaFunctionNamingConventions:
    """Tests for Lambda function naming conventions."""

    def test_export_function_name_is_pascalcase(self):
        """Verify SessionsExport function name follows PascalCase."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'SessionsExport' in content

    def test_crawler_trigger_function_name_is_pascalcase(self):
        """Verify SessionsCrawlerTrigger function name follows PascalCase."""
        locals_tf = SESSIONS_SRC_PATH / "locals.tf"
        content = locals_tf.read_text()
        assert 'SessionsCrawlerTrigger' in content


class TestLambdaConfiguration:
    """Tests for Lambda configuration in Terraform."""

    def test_handler_lambda_uses_arm64_architecture(self):
        """Verify handler Lambda uses arm64 architecture."""
        lambda_tf = SESSIONS_SRC_PATH / "lambda.tf"
        content = lambda_tf.read_text()
        assert 'arm64' in content

    def test_handler_lambda_uses_python313_runtime(self):
        """Verify handler Lambda uses Python 3.13 runtime."""
        lambda_tf = SESSIONS_SRC_PATH / "lambda.tf"
        content = lambda_tf.read_text()
        assert 'python3.13' in content

    def test_export_lambda_uses_arm64_architecture(self):
        """Verify export Lambda uses arm64 architecture."""
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert 'arm64' in content

    def test_export_lambda_uses_python313_runtime(self):
        """Verify export Lambda uses Python 3.13 runtime."""
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert 'python3.13' in content
