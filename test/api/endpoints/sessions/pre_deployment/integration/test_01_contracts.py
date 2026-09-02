import re
from typing import Optional, Set

from repo_utils import REPO_ROOT


SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"
SESSIONS_TRACKER_PATH = SESSIONS_SRC_PATH / "lambda" / "tracker"
SESSIONS_EXPORTER_PATH = SESSIONS_SRC_PATH / "lambda" / "exporter"
SESSIONS_IAM_TF_PATH = SESSIONS_SRC_PATH / "iam.tf"
TRACKER_HANDLER_PATH = SESSIONS_TRACKER_PATH / "handler.py"


class TestLambdaHandlerContracts:
    def test_handler_exports_lambda_handler_function(self) -> None:
        handler_py = SESSIONS_TRACKER_PATH / "handler.py"
        content = handler_py.read_text()
        assert "def lambda_handler(" in content

    def test_export_handler_exports_lambda_handler_function(self) -> None:
        export_py = SESSIONS_EXPORTER_PATH / "handler.py"
        content = export_py.read_text()
        assert "def lambda_handler(" in content


class TestTerraformLambdaContracts:
    def test_lambda_tf_references_correct_handler_path(self) -> None:
        lambda_tf = SESSIONS_SRC_PATH / "lambda.tf"
        content = lambda_tf.read_text()
        assert "handler.lambda_handler" in content

    def test_analytics_tf_references_correct_export_handler_path(self) -> None:
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert "handler.lambda_handler" in content


class TestEnvironmentVariableContracts:
    def test_handler_uses_session_events_table_env_var(self) -> None:
        handler_py = SESSIONS_TRACKER_PATH / "handler.py"
        content = handler_py.read_text()
        assert "SESSION_EVENTS_TABLE" in content

    def test_lambda_tf_provides_session_events_table_env_var(self) -> None:
        lambda_tf = SESSIONS_SRC_PATH / "lambda.tf"
        content = lambda_tf.read_text()
        assert "SESSION_EVENTS_TABLE" in content

    def test_export_handler_uses_dynamodb_table_arn_env_var(self) -> None:
        export_py = SESSIONS_EXPORTER_PATH / "handler.py"
        content = export_py.read_text()
        assert "DYNAMODB_TABLE_ARN" in content

    def test_export_handler_uses_s3_bucket_env_var(self) -> None:
        export_py = SESSIONS_EXPORTER_PATH / "handler.py"
        content = export_py.read_text()
        assert "S3_BUCKET" in content

    def test_export_handler_uses_s3_prefix_env_var(self) -> None:
        export_py = SESSIONS_EXPORTER_PATH / "handler.py"
        content = export_py.read_text()
        assert "S3_PREFIX" in content

    def test_analytics_tf_provides_dynamodb_table_arn_env_var(self) -> None:
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert "DYNAMODB_TABLE_ARN" in content

    def test_analytics_tf_provides_s3_bucket_env_var(self) -> None:
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert "S3_BUCKET" in content

    def test_analytics_tf_provides_s3_prefix_env_var(self) -> None:
        analytics_tf = SESSIONS_SRC_PATH / "analytics.tf"
        content = analytics_tf.read_text()
        assert "S3_PREFIX" in content


def _dynamodb_access_policy_block() -> Optional[re.Match[str]]:
    return re.search(
        r'resource\s+"aws_iam_role_policy"\s+"dynamodb_access"\s*\{.*?\n\}',
        SESSIONS_IAM_TF_PATH.read_text(),
        re.DOTALL,
    )


def _dynamodb_client_methods_granted_by_iam_tf() -> Set[str]:
    policy = _dynamodb_access_policy_block()
    granted = re.findall(r'"dynamodb:(\w+)"', policy.group(0) if policy else "")
    return {re.sub(r"(?<!^)([A-Z])", r"_\1", action).lower() for action in granted}


def _dynamodb_client_methods_called_by_tracker_handler() -> Set[str]:
    handler = TRACKER_HANDLER_PATH.read_text()
    aliases = sorted(set(re.findall(r"(\w+)\s*=\s*get_dynamodb_client\(\)", handler)))
    receivers = "|".join([r"get_dynamodb_client\(\)"] + [re.escape(a) for a in aliases])
    return set(re.findall(rf"(?:{receivers})\.(\w+)\(", handler))


class TestIamPolicyContracts:
    def test_iam_tf_declares_the_dynamodb_access_policy(self) -> None:
        assert _dynamodb_access_policy_block(), (
            "aws_iam_role_policy.dynamodb_access not found in iam.tf"
        )

    def test_dynamodb_actions_granted_are_the_ones_the_tracker_calls(self) -> None:
        granted = _dynamodb_client_methods_granted_by_iam_tf()
        called = _dynamodb_client_methods_called_by_tracker_handler()
        assert granted == called, (
            f"iam.tf grants DynamoDB actions no tracker call needs: "
            f"{sorted(granted - called)}; the tracker calls DynamoDB methods "
            f"iam.tf does not grant: {sorted(called - granted)}"
        )
