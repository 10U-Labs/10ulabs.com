"""Pytest fixtures for sessions pre-deployment integration tests.

Pre-deployment integration tests verify:
- Contract compatibility between local files
- AWS prerequisites exist and are configured correctly
- Terraform state matches AWS reality
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
def sessions_config(request):
    """Get sessions terraform configuration.

    Parses locals.tf to extract resource naming conventions.
    """
    if not request.getfixturevalue("sessions_terraform_initialized"):
        pytest.skip("Terraform init failed for sessions")

    locals_tf = SESSIONS_SRC_PATH / "locals.tf"
    content = locals_tf.read_text()

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


