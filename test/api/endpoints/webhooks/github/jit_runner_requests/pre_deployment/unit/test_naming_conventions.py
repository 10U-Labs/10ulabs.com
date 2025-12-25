"""Unit tests to verify IAM role, Lambda function, and SQS queue names use PascalCase.

These tests parse Terraform files to validate naming conventions before deployment.
Names must use PascalCase (no dashes, underscores, or other separators).
"""

from naming_conventions.test_helpers import (
    create_iam_role_tests,
    create_lambda_function_tests,
    create_sqs_queue_tests,
)
from repo_utils import REPO_ROOT
from terraform_config import (
    extract_iam_role_names,
    extract_lambda_function_names,
    extract_sqs_queue_names,
)

RUNNERS_SRC = (
    REPO_ROOT / "src" / "api" / "endpoints" / "webhooks" / "github" / "jit_runner_requests"
)

IAM_ROLES = extract_iam_role_names(RUNNERS_SRC / "iam.tf")
LAMBDA_FUNCTIONS = extract_lambda_function_names(
    RUNNERS_SRC / "lambda.tf", use_handler_names=True
)
SQS_QUEUES = extract_sqs_queue_names(RUNNERS_SRC / "sqs.tf")

assert IAM_ROLES, "Failed to extract IAM roles from runners Terraform files"
assert LAMBDA_FUNCTIONS, "Failed to extract Lambda functions from runners Terraform files"
assert SQS_QUEUES, "Failed to extract SQS queues from runners Terraform files"

TestIAMRoleNamingConventions = create_iam_role_tests(IAM_ROLES)
TestLambdaFunctionNamingConventions = create_lambda_function_tests(LAMBDA_FUNCTIONS)
TestSQSQueueNamingConventions = create_sqs_queue_tests(SQS_QUEUES)
