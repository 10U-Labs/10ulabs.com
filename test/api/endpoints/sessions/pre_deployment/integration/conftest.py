import pytest


@pytest.fixture(scope="module")
def sessions_config(request):
    if not request.getfixturevalue("sessions_terraform_initialized"):
        pytest.skip("Terraform init failed for sessions")

    return {
        "lambda_handler_name": "TenULabsSessionsHandler",
        "export_function_name": "TenULabsSessionsExport",
        "handler_role_name": "TenULabsSessionsHandlerRole",
        "export_role_name": "TenULabsSessionsExportRole",
        "scheduler_role_name": "TenULabsSessionsSchedulerRole",
        "dynamodb_table_name": "TenULabs-session-events",
        "s3_bucket_name": "tenulabs-sessions-analytics",
    }
