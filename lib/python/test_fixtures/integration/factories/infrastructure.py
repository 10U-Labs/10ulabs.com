from typing import Any, Dict, Tuple

import pytest
from repo_utils import REPO_ROOT
from test_fixtures.integration.helpers import aws_call_error
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
