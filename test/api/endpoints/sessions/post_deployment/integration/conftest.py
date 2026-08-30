import pytest


@pytest.fixture(scope="module")
def sessions_config():
    return {
        "handler_function_name": "TenULabsSessionsHandler",
        "export_function_name": "TenULabsSessionsExport",
        "handler_role_name": "TenULabsSessionsHandlerRole",
        "export_role_name": "TenULabsSessionsExportRole",
        "scheduler_role_name": "TenULabsSessionsSchedulerRole",
        "backup_role_name": "TenULabsSessionsBackupRole",
        "dynamodb_table_name": "TenULabs-session-events",
        "s3_bucket_name": "tenulabs-sessions-analytics",
        "backup_vault_name": "TenULabs-sessions-backup",
        "backup_plan_name": "TenULabs-sessions-backup",
        "scheduler_name": "TenULabs-SessionsDailyExport",
        "handler_log_group": "/aws/lambda/TenULabsSessionsHandler",
        "export_log_group": "/aws/lambda/TenULabsSessionsExport",
    }
