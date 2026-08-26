from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import create_naming_conventions_tests

HEALTH_SRC = REPO_ROOT / "src" / "api" / "operational" / "health"

_test_classes = create_naming_conventions_tests(endpoint_src=HEALTH_SRC)
globals()['TestIAMRoleNamingConventions'] = _test_classes[0]
globals()['TestLambdaFunctionNamingConventions'] = _test_classes[1]
