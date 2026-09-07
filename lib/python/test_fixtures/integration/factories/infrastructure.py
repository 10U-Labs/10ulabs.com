from typing import Any, Callable, Dict, Tuple

from botocore.exceptions import ClientError
import pytest
from repo_utils import REPO_ROOT
from test_fixtures.integration.helpers import (
    aws_call_error,
    iam_role_problem,
    role_policy_problem,
)
from test_fixtures.terraform import terraform_init, terraform_output


def create_www_common_fixtures(
    include_cloudfront: bool = False,
    include_website_domain: bool = False,
) -> Tuple[Any, Any]:
    www_common_dir = REPO_ROOT / "src" / "www" / "common"

    @pytest.fixture(scope="session")
    def www_common_terraform_initialized() -> bool:
        return terraform_init(www_common_dir)

    @pytest.fixture(scope="session")
    def www_common_outputs(request: pytest.FixtureRequest) -> Dict[str, str]:
        if not request.getfixturevalue("www_common_terraform_initialized"):
            pytest.skip("Terraform init failed for www_common")
        outputs = {
            "bucket_name": terraform_output(www_common_dir, "bucket_name"),
            "bucket_arn": terraform_output(www_common_dir, "bucket_arn"),
        }
        if include_website_domain:
            outputs["website_domain_name"] = terraform_output(
                www_common_dir, "website_domain_name"
            )
        if include_cloudfront:
            outputs["cloudfront_distribution_id"] = terraform_output(
                www_common_dir, "cloudfront_distribution_id"
            )
        return outputs

    return www_common_terraform_initialized, www_common_outputs


def create_www_common_s3_existence_tests() -> type:
    class TestWWWCommonS3Existence:
        def test_bucket_name_output_exists(self, www_common_outputs: Dict[str, str]) -> None:
            assert www_common_outputs.get("bucket_name"), (
                "bucket_name output not found in www_common. "
                "Run terraform apply in src/www/common/"
            )

        def test_s3_bucket_exists(self, s3_client: Any, www_common_outputs: Dict[str, str]) -> None:
            bucket_name = www_common_outputs.get("bucket_name")
            if not bucket_name:
                pytest.skip("bucket_name output not available")
            error = aws_call_error(lambda: s3_client.head_bucket(Bucket=bucket_name))
            assert not error, (
                f"S3 bucket '{bucket_name}' is not reachable: {error}. "
                "Run terraform apply in src/www/common/"
            )

    return TestWWWCommonS3Existence


def handle_ecr_error(error: ClientError, operation: str, repository_name: str) -> None:
    error_code = error.response["Error"]["Code"]
    if error_code == "RepositoryNotFoundException":
        pytest.skip("Repository does not exist")
    if error_code == "AccessDeniedException":
        pytest.fail(
            f"No permission to call {operation} on '{repository_name}'. "
            "This is required to manage Docker images."
        )
    raise error


def create_log_group_configuration_tests(
    log_group_fixture: str,
    expected_retention: int = 7,
) -> type:
    class TestCloudWatchLogsConfiguration:
        def test_handler_log_group_has_retention_set(self, request: pytest.FixtureRequest) -> None:
            log_group = request.getfixturevalue(log_group_fixture)
            assert log_group["retention"] is not None, (
                f"Log group '{log_group['name']}' should have retention set"
            )

        def test_handler_log_group_retention_is_expected(
            self,
            request: pytest.FixtureRequest
        ) -> None:
            log_group = request.getfixturevalue(log_group_fixture)
            retention = log_group["retention"]
            assert retention == expected_retention, (
                f"Log group retention should be {expected_retention} days, got: {retention}"
            )

    return TestCloudWatchLogsConfiguration


def create_lambda_role_existence_test(
    role_name_fixture: str,
    terraform_path: str
) -> Callable[..., None]:
    def test_lambda_execution_role_exists(
        _self: Any,
        iam_client: Any,
        request: pytest.FixtureRequest
    ) -> None:
        role_name = request.getfixturevalue(role_name_fixture)
        problem = iam_role_problem(iam_client, role_name, terraform_path)
        assert not problem, problem
    return test_lambda_execution_role_exists


def create_kms_policy_test(role_name_fixture: str) -> Callable[..., None]:
    def test_lambda_role_has_kms_policy(
        _self: Any,
        iam_client: Any,
        request: pytest.FixtureRequest
    ) -> None:
        role_name = request.getfixturevalue(role_name_fixture)
        problem = role_policy_problem(iam_client, role_name, "KMSDecrypt")
        assert not problem, problem
    return test_lambda_role_has_kms_policy
