import re
from typing import Optional, Set

from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import create_lambda_source_contract_tests


SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"
SESSIONS_TRACKER_PATH = SESSIONS_SRC_PATH / "lambda" / "tracker"
SESSIONS_IAM_TF_PATH = SESSIONS_SRC_PATH / "iam.tf"
TRACKER_HANDLER_PATH = SESSIONS_TRACKER_PATH / "handler.py"


TestTrackerLambdaSourceContract = create_lambda_source_contract_tests(
    endpoint_src=SESSIONS_SRC_PATH,
    tf_file="lambda.tf",
    resource_name="handler",
)

TestExporterLambdaSourceContract = create_lambda_source_contract_tests(
    endpoint_src=SESSIONS_SRC_PATH,
    tf_file="analytics.tf",
    resource_name="export",
)


def _dynamodb_access_policy_block() -> Optional[re.Match[str]]:
    return re.search(
        r'resource\s+"aws_iam_role_policy"\s+"dynamodb_access"\s*\{.*?\n\}',
        SESSIONS_IAM_TF_PATH.read_text(),
        re.DOTALL,
    )


def _dynamodb_client_methods_granted_by_iam_tf() -> Set[str]:
    policy = _dynamodb_access_policy_block()
    granted = re.findall(r'"dynamodb:(\w+)"', policy.group(0) if policy else "")
    return {re.sub(r"(?<!^)([A-Z])", r"_\1", action).lower() for action in granted}


def _dynamodb_client_methods_called_by_tracker_handler() -> Set[str]:
    handler = TRACKER_HANDLER_PATH.read_text()
    aliases = sorted(set(re.findall(r"(\w+)\s*=\s*get_dynamodb_client\(\)", handler)))
    receivers = "|".join([r"get_dynamodb_client\(\)"] + [re.escape(a) for a in aliases])
    return set(re.findall(rf"(?:{receivers})\.(\w+)\(", handler))


class TestIamPolicyContracts:
    def test_iam_tf_declares_the_dynamodb_access_policy(self) -> None:
        assert _dynamodb_access_policy_block(), (
            "aws_iam_role_policy.dynamodb_access not found in iam.tf"
        )

    def test_dynamodb_actions_granted_are_the_ones_the_tracker_calls(self) -> None:
        granted = _dynamodb_client_methods_granted_by_iam_tf()
        called = _dynamodb_client_methods_called_by_tracker_handler()
        assert granted == called, (
            f"iam.tf grants DynamoDB actions no tracker call needs: "
            f"{sorted(granted - called)}; the tracker calls DynamoDB methods "
            f"iam.tf does not grant: {sorted(called - granted)}"
        )
