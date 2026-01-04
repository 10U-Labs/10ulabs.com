"""Layer 1: Contract tests for sessions endpoint.

Contract tests verify that local files that must work together are compatible.
No AWS calls are made in these tests.
"""
import pytest

from repo_utils import REPO_ROOT

pytestmark = pytest.mark.layer(1)

SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"
SESSIONS_LAMBDA_PATH = SESSIONS_SRC_PATH / "lambda"
SESSIONS_LAMBDAS_PATH = SESSIONS_SRC_PATH / "lambdas"


class TestLambdaHandlerContracts:
    """Tests for Lambda handler contract compatibility."""

    def test_handler_exports_lambda_handler_function(self):
        """Verify handler.py exports lambda_handler function."""
        handler_py = SESSIONS_LAMBDA_PATH / "handler.py"
        content = handler_py.read_text()
        assert "def lambda_handler(" in content

    def test_export_handler_exports_lambda_handler_function(self):
        """Verify export_handler.py exports lambda_handler function."""
        export_py = SESSIONS_LAMBDAS_PATH / "export_handler.py"
        content = export_py.read_text()
        assert "def lambda_handler(" in content

    def test_crawler_trigger_exports_lambda_handler_function(self):
        """Verify crawler_trigger.py exports lambda_handler function."""
        crawler_py = SESSIONS_LAMBDAS_PATH / "crawler_trigger.py"
        content = crawler_py.read_text()
        assert "def lambda_handler(" in content


class TestTerraformLambdaContracts:
    """Tests for Terraform Lambda configuration contracts."""

    def test_lambda_tf_references_correct_handler_path(self):
        """Verify lambda.tf handler matches source file structure."""
        lambda_tf = SESSIONS_SRC_PATH / "lambda.tf"
        content = lambda_tf.read_text()
        assert "handler.lambda_handler" in content

    def test_analytics_tf_references_correct_export_handler_path(self):
        """Verify analytics.tf export handler matches source file structure."""
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert "export_handler.lambda_handler" in content

    def test_analytics_tf_references_correct_crawler_trigger_path(self):
        """Verify analytics.tf crawler trigger handler matches source."""
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert "crawler_trigger.lambda_handler" in content


class TestEnvironmentVariableContracts:
    """Tests for environment variable contracts between handler and Terraform."""

    def test_handler_uses_session_events_table_env_var(self):
        """Verify handler.py uses SESSION_EVENTS_TABLE environment variable."""
        handler_py = SESSIONS_LAMBDA_PATH / "handler.py"
        content = handler_py.read_text()
        assert "SESSION_EVENTS_TABLE" in content

    def test_lambda_tf_provides_session_events_table_env_var(self):
        """Verify lambda.tf provides SESSION_EVENTS_TABLE environment variable."""
        lambda_tf = SESSIONS_SRC_PATH / "lambda.tf"
        content = lambda_tf.read_text()
        assert "SESSION_EVENTS_TABLE" in content

    def test_export_handler_uses_dynamodb_table_arn_env_var(self):
        """Verify export_handler.py uses DYNAMODB_TABLE_ARN environment variable."""
        export_py = SESSIONS_LAMBDAS_PATH / "export_handler.py"
        content = export_py.read_text()
        assert "DYNAMODB_TABLE_ARN" in content

    def test_export_handler_uses_s3_bucket_env_var(self):
        """Verify export_handler.py uses S3_BUCKET environment variable."""
        export_py = SESSIONS_LAMBDAS_PATH / "export_handler.py"
        content = export_py.read_text()
        assert "S3_BUCKET" in content

    def test_export_handler_uses_s3_prefix_env_var(self):
        """Verify export_handler.py uses S3_PREFIX environment variable."""
        export_py = SESSIONS_LAMBDAS_PATH / "export_handler.py"
        content = export_py.read_text()
        assert "S3_PREFIX" in content

    def test_analytics_tf_provides_dynamodb_table_arn_env_var(self):
        """Verify analytics.tf provides DYNAMODB_TABLE_ARN environment variable."""
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert "DYNAMODB_TABLE_ARN" in content

    def test_analytics_tf_provides_s3_bucket_env_var(self):
        """Verify analytics.tf provides S3_BUCKET environment variable."""
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert "S3_BUCKET" in content

    def test_analytics_tf_provides_s3_prefix_env_var(self):
        """Verify analytics.tf provides S3_PREFIX environment variable."""
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert "S3_PREFIX" in content

    def test_crawler_trigger_uses_crawler_name_env_var(self):
        """Verify crawler_trigger.py uses CRAWLER_NAME environment variable."""
        crawler_py = SESSIONS_LAMBDAS_PATH / "crawler_trigger.py"
        content = crawler_py.read_text()
        assert "CRAWLER_NAME" in content

    def test_analytics_tf_provides_crawler_name_env_var(self):
        """Verify analytics.tf provides CRAWLER_NAME environment variable."""
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert "CRAWLER_NAME" in content
