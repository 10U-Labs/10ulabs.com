from repo_utils import REPO_ROOT


SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"
SESSIONS_TRACKER_PATH = SESSIONS_SRC_PATH / "lambda" / "tracker"
SESSIONS_EXPORTER_PATH = SESSIONS_SRC_PATH / "lambda" / "exporter"


class TestLambdaHandlerContracts:
    def test_handler_exports_lambda_handler_function(self):
        handler_py = SESSIONS_TRACKER_PATH / "handler.py"
        content = handler_py.read_text()
        assert "def lambda_handler(" in content

    def test_export_handler_exports_lambda_handler_function(self):
        export_py = SESSIONS_EXPORTER_PATH / "handler.py"
        content = export_py.read_text()
        assert "def lambda_handler(" in content


class TestTerraformLambdaContracts:
    def test_lambda_tf_references_correct_handler_path(self):
        lambda_tf = SESSIONS_SRC_PATH / "lambda.tf"
        content = lambda_tf.read_text()
        assert "handler.lambda_handler" in content

    def test_analytics_tf_references_correct_export_handler_path(self):
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert "handler.lambda_handler" in content


class TestEnvironmentVariableContracts:
    def test_handler_uses_session_events_table_env_var(self):
        handler_py = SESSIONS_TRACKER_PATH / "handler.py"
        content = handler_py.read_text()
        assert "SESSION_EVENTS_TABLE" in content

    def test_lambda_tf_provides_session_events_table_env_var(self):
        lambda_tf = SESSIONS_SRC_PATH / "lambda.tf"
        content = lambda_tf.read_text()
        assert "SESSION_EVENTS_TABLE" in content

    def test_export_handler_uses_dynamodb_table_arn_env_var(self):
        export_py = SESSIONS_EXPORTER_PATH / "handler.py"
        content = export_py.read_text()
        assert "DYNAMODB_TABLE_ARN" in content

    def test_export_handler_uses_s3_bucket_env_var(self):
        export_py = SESSIONS_EXPORTER_PATH / "handler.py"
        content = export_py.read_text()
        assert "S3_BUCKET" in content

    def test_export_handler_uses_s3_prefix_env_var(self):
        export_py = SESSIONS_EXPORTER_PATH / "handler.py"
        content = export_py.read_text()
        assert "S3_PREFIX" in content

    def test_analytics_tf_provides_dynamodb_table_arn_env_var(self):
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert "DYNAMODB_TABLE_ARN" in content

    def test_analytics_tf_provides_s3_bucket_env_var(self):
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert "S3_BUCKET" in content

    def test_analytics_tf_provides_s3_prefix_env_var(self):
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert "S3_PREFIX" in content
