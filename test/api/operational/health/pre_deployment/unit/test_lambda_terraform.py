"""Unit tests for health endpoint Lambda Terraform configuration."""
from test.api.operational.health.conftest import HEALTH_SRC, REPO_ROOT
from test_fixtures.terraform_tests import create_lambda_terraform_tests


LAMBDA_FILE = HEALTH_SRC / "lambda.tf"
API_BACKEND_SRC = REPO_ROOT / "src" / "api" / "backend"

TestLambdaTerraform = create_lambda_terraform_tests(
    lambda_file=LAMBDA_FILE,
    handler_name="health_handler",
    description="Health check endpoint for API",
)


def test_health_handler_log_subscription_exists():
    """Verify log subscription filter is defined."""
    log_subs_file = API_BACKEND_SRC / "log_subscriptions.tf"
    with open(log_subs_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "health_handler"' in content
