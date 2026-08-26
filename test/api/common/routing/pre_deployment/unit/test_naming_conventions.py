import pytest

from naming_conventions import validate_name
from terraform_config import extract_iam_role_names, extract_lambda_function_names
from repo_utils import REPO_ROOT

BACKEND_SRC = REPO_ROOT / "src" / "api" / "common" / "routing"

IAM_FILES = [
    BACKEND_SRC / "iam.tf",
    BACKEND_SRC / "apigateway.tf",
    BACKEND_SRC / "firehose.tf",
    BACKEND_SRC / "iam_api_gateway_sqs.tf",
]

LAMBDA_FILE = BACKEND_SRC / "lambda.tf"

IAM_ROLES = []
for iam_file in IAM_FILES:
    IAM_ROLES.extend(extract_iam_role_names(iam_file))

LAMBDA_FUNCTIONS = extract_lambda_function_names(LAMBDA_FILE, use_handler_names=True)


class TestIAMRoleNamingConventions:
    @pytest.mark.parametrize(
        "resource_name,role_name",
        IAM_ROLES,
        ids=[f"iam_role_{r[0]}" for r in IAM_ROLES],
    )
    def test_iam_role_name_is_pascalcase(self, resource_name, role_name):
        error = validate_name(role_name)
        assert error is None, (
            f"IAM role '{resource_name}' has invalid name '{role_name}': {error}"
        )

    def test_no_iam_role_names_contain_dashes(self):
        violations = [(r, n) for r, n in IAM_ROLES if '-' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} IAM roles with dashes:\n"
            + "\n".join(f"  - {r}: '{n}'" for r, n in violations)
        )

    def test_no_iam_role_names_contain_underscores(self):
        violations = [(r, n) for r, n in IAM_ROLES if '_' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} IAM roles with underscores:\n"
            + "\n".join(f"  - {r}: '{n}'" for r, n in violations)
        )


class TestLambdaFunctionNamingConventions:
    @pytest.mark.parametrize(
        "resource_name,function_name",
        LAMBDA_FUNCTIONS,
        ids=[f"lambda_{f[0]}" for f in LAMBDA_FUNCTIONS],
    )
    def test_lambda_function_name_is_pascalcase(self, resource_name, function_name):
        error = validate_name(function_name)
        assert error is None, (
            f"Lambda function '{resource_name}' has invalid name '{function_name}': {error}"
        )

    def test_no_lambda_function_names_contain_dashes(self):
        violations = [(r, n) for r, n in LAMBDA_FUNCTIONS if '-' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} Lambda functions with dashes:\n"
            + "\n".join(f"  - {r}: '{n}'" for r, n in violations)
        )

    def test_no_lambda_function_names_contain_underscores(self):
        violations = [(r, n) for r, n in LAMBDA_FUNCTIONS if '_' in n]
        assert len(violations) == 0, (
            f"Found {len(violations)} Lambda functions with underscores:\n"
            + "\n".join(f"  - {r}: '{n}'" for r, n in violations)
        )
