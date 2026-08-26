import pytest

from repo_utils import REPO_ROOT
from test_fixtures.terraform import terraform_output

SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"


@pytest.fixture(scope="module")
def sessions_outputs(request):
    if not request.getfixturevalue("sessions_terraform_initialized"):
        pytest.skip("Terraform init failed for sessions")
    return {
        "lambda_function_name": terraform_output(
            SESSIONS_SRC_PATH, "lambda_function_name"
        ),
        "lambda_function_arn": terraform_output(
            SESSIONS_SRC_PATH, "lambda_function_arn"
        ),
        "dynamodb_table_name": terraform_output(
            SESSIONS_SRC_PATH, "dynamodb_table_name"
        ),
        "dynamodb_table_arn": terraform_output(
            SESSIONS_SRC_PATH, "dynamodb_table_arn"
        ),
    }


@pytest.fixture(scope="module")
def sessions_config():
    return {
        "handler_function_name": "TenULabsSessionsHandler",
        "export_function_name": "TenULabsSessionsExport",
        "handler_role_name": "TenULabsSessionsHandlerRole",
        "export_role_name": "TenULabsSessionsExportRole",
        "scheduler_role_name": "TenULabsSessionsSchedulerRole",
        "backup_role_name": "TenULabs-SessionsBackup-Role",
        "dynamodb_table_name": "TenULabs-session-events",
        "s3_bucket_name": "tenulabs-sessions-analytics",
        "backup_vault_name": "TenULabs-sessions-backup",
        "backup_plan_name": "TenULabs-sessions-backup",
        "scheduler_name": "TenULabs-SessionsDailyExport",
        "handler_log_group": "/aws/lambda/TenULabsSessionsHandler",
        "export_log_group": "/aws/lambda/TenULabsSessionsExport",
    }
