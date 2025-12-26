"""Unit tests for Lambda lifecycle configuration."""

from repo_utils import REPO_ROOT
from test_fixtures.lambda_lifecycle import create_lambda_lifecycle_tests


ENDPOINT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ecs" / "images"

TestLambdaLifecycle = create_lambda_lifecycle_tests(endpoint_src=ENDPOINT_SRC)
