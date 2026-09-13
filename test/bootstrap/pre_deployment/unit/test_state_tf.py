import re
from pathlib import Path

import pytest

VERSIONING = 'resource "aws_s3_bucket_versioning" "terraform_state"'
LIFECYCLE = 'resource "aws_s3_bucket_lifecycle_configuration" "terraform_state"'
POLICY = 'resource "aws_s3_bucket_policy" "terraform_state"'


@pytest.fixture(name='state_tf')
def state_tf_fixture(bootstrap_dir: Path) -> str:
    return (bootstrap_dir / 'state.tf').read_text(encoding='utf-8')


@pytest.fixture(name='wan_synthesizer_tf')
def wan_synthesizer_tf_fixture(bootstrap_dir: Path) -> str:
    return (bootstrap_dir / 'wan_synthesizer.tf').read_text(encoding='utf-8')


def _block(content: str, header: str) -> str:
    start = content.index(header)
    return content[start:content.index('\n}\n', start)]


def test_state_bucket_keeps_every_version_of_every_state(state_tf: str) -> None:
    assert 'status = "Enabled"' in _block(state_tf, VERSIONING)


def test_state_bucket_expires_noncurrent_versions_at_ninety_days(state_tf: str) -> None:
    assert 'noncurrent_days = 90' in _block(state_tf, LIFECYCLE)


def test_state_bucket_policy_denies_every_principal_it_does_not_name(state_tf: str) -> None:
    assert '"aws:PrincipalArn"' in _block(state_tf, POLICY)


def test_state_bucket_policy_names_the_wan_synthesizer_deploy_role(state_tf: str) -> None:
    assert 'local.name_for_wan_synthesizer_role' in _block(state_tf, POLICY)


def test_bootstrap_declares_no_resource_for_the_wan_synthesizer_role(
    wan_synthesizer_tf: str
) -> None:
    assert not re.search(r'^resource ', wan_synthesizer_tf, re.MULTILINE)
