"""Pytest fixtures for sessions post-deployment integration tests.

Post-deployment integration tests verify:
- Resources created by terraform apply exist
- Resources are configured correctly
- Components are properly wired together
"""
import pytest

from repo_utils import REPO_ROOT
from test_fixtures.terraform import terraform_init, terraform_output

SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"
API_COMMON_ROUTING_PATH = REPO_ROOT / "src" / "api" / "common" / "routing"


@pytest.fixture(scope="module")
def sessions_terraform_initialized():
    """Initialize terraform for sessions state access."""
    return terraform_init(SESSIONS_SRC_PATH)


@pytest.fixture(scope="module")
def sessions_outputs(request):
    """Get sessions terraform outputs."""
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
    """Get sessions configuration for testing.

    Provides expected resource names based on naming conventions.
    """
    return {
        "handler_function_name": "TenULabsSessionsHandler",
        "export_function_name": "TenULabsSessionsExport",
        "crawler_trigger_function_name": "TenULabsSessionsCrawlerTrigger",
        "handler_role_name": "TenULabsSessionsHandlerRole",
        "export_role_name": "TenULabsSessionsExportRole",
        "crawler_trigger_role_name": "TenULabsSessionsCrawlerTriggerRole",
        "glue_crawler_role_name": "TenULabsSessionsGlueCrawlerRole",
        "scheduler_role_name": "TenULabsSessionsSchedulerRole",
        "backup_role_name": "TenULabsSessionsBackup-Role",
        "dynamodb_table_name": "TenULabs-session-events",
        "s3_bucket_name": "tenulabs-sessions-analytics",
        "glue_database_name": "tenulabs_sessions_analytics",
        "glue_crawler_name": "TenULabs-sessions-events",
        "backup_vault_name": "TenULabs-sessions-backup",
        "backup_plan_name": "TenULabs-sessions-backup",
        "scheduler_name": "TenULabs-SessionsDailyExport",
        "eventbridge_rule_name": "TenULabs-SessionsExportCompleted",
        "handler_log_group": "/aws/lambda/TenULabsSessionsHandler",
        "export_log_group": "/aws/lambda/TenULabsSessionsExport",
        "crawler_trigger_log_group": "/aws/lambda/TenULabsSessionsCrawlerTrigger",
    }


@pytest.fixture(scope="module")
def api_common_routing_initialized():
    """Initialize terraform for api_common_routing state access."""
    return terraform_init(API_COMMON_ROUTING_PATH)


@pytest.fixture(scope="module")
def api_gateway_id(request):
    """Get API Gateway ID from api_common_routing outputs."""
    if not request.getfixturevalue("api_common_routing_initialized"):
        pytest.skip("Terraform init failed for api_common_routing")
    return terraform_output(API_COMMON_ROUTING_PATH, "api_gateway_id")


