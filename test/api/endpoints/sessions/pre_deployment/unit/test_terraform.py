from repo_utils import REPO_ROOT
from test_fixtures.lambda_lifecycle import create_lambda_lifecycle_tests
from test_fixtures.terraform_tests import create_remote_state_config_tests

SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"


TestLambdaLifecycle = create_lambda_lifecycle_tests(
    endpoint_src=SESSIONS_SRC_PATH,
    tf_files=["lambda.tf", "analytics.tf"]
)

TestRemoteStateConfig = create_remote_state_config_tests(
    endpoint_src=SESSIONS_SRC_PATH,
    endpoint_name="sessions"
)
