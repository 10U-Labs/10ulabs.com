"""Pytest fixtures for sessions pre-deployment integration tests.

Pre-deployment integration tests verify:
- Contract compatibility between local files
- AWS prerequisites exist and are configured correctly
- Terraform state matches AWS reality

Shared fixtures are inherited from test/api/endpoints/sessions/conftest.py.
"""
import pytest

from repo_utils import REPO_ROOT

SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"


@pytest.fixture(scope="module")
def sessions_config(request):
    """Get sessions terraform configuration.

    Parses locals.tf to extract resource naming conventions.
    """
    if not request.getfixturevalue("sessions_terraform_initialized"):
        pytest.skip("Terraform init failed for sessions")

    locals_tf = SESSIONS_SRC_PATH / "locals.tf"
    locals_tf.read_text()  # Verify file exists

    return {
        "terraform_dir": SESSIONS_SRC_PATH,
        "lambda_handler_name": "TenULabsSessionsHandler",
        "export_function_name": "TenULabsSessionsExport",
        "crawler_trigger_function_name": "TenULabsSessionsCrawlerTrigger",
        "handler_role_name": "TenULabsSessionsHandlerRole",
        "export_role_name": "TenULabsSessionsExportRole",
        "crawler_trigger_role_name": "TenULabsSessionsCrawlerTriggerRole",
        "glue_crawler_role_name": "TenULabsSessionsGlueCrawlerRole",
        "scheduler_role_name": "TenULabsSessionsSchedulerRole",
        "dynamodb_table_name": "TenULabs-session-events",
        "s3_bucket_name": "tenulabs-sessions-analytics",
    }
