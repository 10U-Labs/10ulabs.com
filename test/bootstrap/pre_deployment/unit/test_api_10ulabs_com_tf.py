import re
from pathlib import Path

import pytest

API_REPOSITORY = '"${local.github_org}@240548037/api.10ulabs.com@1368777392"'
API_SUBJECT = '"repo:${local.api_repository}:ref:refs/heads/main"'
SUB_CLAIM = "token.actions.githubusercontent.com:sub"
SUB_CONDITION = rf'test\s*=\s*"StringEquals"\s*variable\s*=\s*"{SUB_CLAIM}"'


@pytest.fixture(name='api_tf')
def api_tf_fixture(bootstrap_dir: Path) -> str:
    return (bootstrap_dir / 'api_10ulabs_com.tf').read_text(encoding='utf-8')


def test_api_deploy_role_names_the_repository_by_its_immutable_ids(api_tf: str) -> None:
    assert API_REPOSITORY in api_tf


def test_api_deploy_role_trusts_the_subject_on_main_alone(api_tf: str) -> None:
    assert API_SUBJECT in api_tf


def test_api_deploy_role_trust_matches_the_subject_exactly(api_tf: str) -> None:
    assert re.search(SUB_CONDITION, api_tf)


def test_api_deploy_role_carries_no_managed_policy(api_tf: str) -> None:
    assert 'aws_iam_role_policy_attachment' not in api_tf


def test_api_deploy_role_writes_only_its_own_repository_state(api_tf: str) -> None:
    assert '"${aws_s3_bucket.terraform_state.arn}/api.10ulabs.com/*"' in api_tf


def test_api_deploy_role_may_reconcile_itself(api_tf: str) -> None:
    assert '"iam:PutRolePolicy"' in api_tf


def test_api_deploy_role_may_describe_itself(api_tf: str) -> None:
    assert '"iam:UpdateRoleDescription"' in api_tf
