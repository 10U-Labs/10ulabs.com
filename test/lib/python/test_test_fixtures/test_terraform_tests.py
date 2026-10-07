from pathlib import Path
from typing import Callable
from unittest.mock import patch

import pytest

from test_fixtures.terraform_tests import create_state_lock_contract_tests
from test_fixtures.outcomes import accepted


def _state_lock_stack(tmp_path: Path, key: str, group: str) -> Path:
    stack_src = tmp_path / "stack"
    stack_src.mkdir()
    (stack_src / "backend.tf").write_text(
        'terraform {\n  backend "s3" {\n' + key + '\n  }\n}\n'
    )
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "a_stack.yml").write_text(
        "name: a_stack\nconcurrency:\n" + group + "\n  cancel-in-progress: false\n"
    )
    return stack_src


def _state_lock_test(tmp_path: Path, key: str, group: str) -> Callable[[], None]:
    stack_src = _state_lock_stack(tmp_path, key, group)
    with patch("test_fixtures.terraform_tests.REPO_ROOT", tmp_path):
        return create_state_lock_contract_tests(stack_src, "a_stack.yml")


ALIGNED_KEY = '    key = "api/operational/health/terraform.tfstate"'
ALIGNED_GROUP = "  group: api/operational/health/terraform.tfstate"


def test_create_state_lock_contract_tests_returns_callable(tmp_path: Path) -> None:
    assert callable(_state_lock_test(tmp_path, ALIGNED_KEY, ALIGNED_GROUP))


def test_create_state_lock_contract_tests_returned_test_name(tmp_path: Path) -> None:
    returned = _state_lock_test(tmp_path, ALIGNED_KEY, ALIGNED_GROUP)
    assert returned.__name__ == "test_group_names_the_state_file"


def test_state_lock_passes_when_key_and_group_agree(tmp_path: Path) -> None:
    assert accepted(_state_lock_test(tmp_path, ALIGNED_KEY, ALIGNED_GROUP))


def test_state_lock_fails_when_group_names_another_state_file(tmp_path: Path) -> None:
    returned = _state_lock_test(
        tmp_path, ALIGNED_KEY, "  group: api/operational/diagnostics/terraform.tfstate"
    )
    with pytest.raises(AssertionError):
        returned()


def test_state_lock_fails_when_key_names_another_state_file(tmp_path: Path) -> None:
    returned = _state_lock_test(
        tmp_path, '    key = "www/common/terraform.tfstate"', ALIGNED_GROUP
    )
    with pytest.raises(AssertionError):
        returned()


def test_state_lock_fails_when_backend_declares_no_key(tmp_path: Path) -> None:
    returned = _state_lock_test(tmp_path, '    region = "us-east-1"', ALIGNED_GROUP)
    with pytest.raises(AssertionError, match="backend.tf declares no key"):
        returned()


def test_state_lock_fails_when_workflow_declares_no_group(tmp_path: Path) -> None:
    returned = _state_lock_test(tmp_path, ALIGNED_KEY, "  cancel-in-progress: true")
    with pytest.raises(AssertionError, match="a_stack.yml declares no concurrency group"):
        returned()


def test_state_lock_message_calls_the_equality_a_naming_convention(tmp_path: Path) -> None:
    returned = _state_lock_test(
        tmp_path, ALIGNED_KEY, "  group: www/common/terraform.tfstate"
    )
    with pytest.raises(AssertionError, match="naming convention"):
        returned()
