import re

import pytest

from repo_utils import REPO_ROOT

SEARCH_ROOTS = (REPO_ROOT / "src", REPO_ROOT / "lib")


DECLARED_OUTPUTS = [
    ("common", "admin_iam_user"),
    ("common", "aws_account_id"),
    ("common", "aws_region"),
    ("common", "domain_name"),
    ("common", "github_app"),
    ("common", "github_org"),
    ("common", "kms_lambda_key_arn"),
    ("common", "lambda_handler_names"),
    ("common", "name_for_central_logs_bucket"),
    ("common", "name_for_github_repo"),
    ("common", "name_for_terraform_state_bucket"),
    ("common", "resource_prefix"),
    ("common", "ssm_github_pat_name"),
    ("s3_bucket", "bucket_arn"),
    ("s3_bucket", "bucket_id"),
    ("s3_bucket", "bucket_regional_domain_name"),
]


def _reading_files(output_name: str) -> list:
    reference = re.compile(rf"module\.\w+\.{re.escape(output_name)}\b")
    return sorted(
        path
        for root in SEARCH_ROOTS
        for path in root.rglob("*.tf")
        if reference.search(path.read_text(encoding="utf-8"))
    )


@pytest.mark.parametrize("module_name,output_name", DECLARED_OUTPUTS)
def test_output_is_read_by_a_stack(module_name: str, output_name: str) -> None:
    assert _reading_files(output_name), (
        f"lib/terraform/{module_name} declares output {output_name} but no .tf "
        f"file under src/ or lib/ writes module.<name>.{output_name}, so "
        f"nothing consumes the value it publishes"
    )
