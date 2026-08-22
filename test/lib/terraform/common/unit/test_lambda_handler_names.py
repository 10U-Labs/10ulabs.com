"""Tests that every shared Lambda handler name is claimed by a stack.

The common module publishes one map, lambda_handler_names, so that the stack
that creates a Lambda and the stack that routes to it spell the name the same
way. A key nobody reads is a name for a function no stack creates, which is
what a deleted endpoint leaves behind: the map still offers the name, and the
only thing still asking for it is a route that can never be answered.
"""
import pytest

from repo_utils import REPO_ROOT
from terraform_config import parse_lambda_handler_names

SRC_ROOT = REPO_ROOT / "src"


def _referencing_files(handler_key: str) -> list:
    """List the Terraform files under src/ that read one handler name."""
    reference = f"lambda_handler_names.{handler_key}"
    return sorted(
        path for path in SRC_ROOT.rglob("*.tf")
        if reference in path.read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("handler_key", sorted(parse_lambda_handler_names()))
def test_handler_name_is_read_by_a_stack(handler_key: str) -> None:
    """Test that some Terraform file under src/ reads this handler name."""
    assert _referencing_files(handler_key), (
        f"lambda_handler_names.{handler_key} is declared by the common module "
        f"but read by no .tf file under src/, so no stack creates the function "
        f"it names"
    )
