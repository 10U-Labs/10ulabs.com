"""Tests that every output of the common module is read by some stack.

The common module is where a value lives when more than one stack needs it,
and a stack reaches one by writing module.<name>.<output>. An output nobody
writes is a value the module offers and no stack wants, which is what a
deleted stack leaves behind. Nothing else catches it: an output is a plain
expression, so Terraform validates one that names a resource AWS destroyed
years ago as readily as one that is true, and the error waits until an apply
tries to resolve it.
"""
import re

import pytest

from repo_utils import REPO_ROOT

SEARCH_ROOTS = (REPO_ROOT / "src", REPO_ROOT / "lib")
OUTPUTS_PATH = REPO_ROOT / "lib" / "terraform" / "common" / "outputs.tf"


def _declared_output_names() -> list:
    """List the names the common module's outputs.tf declares."""
    declarations = OUTPUTS_PATH.read_text(encoding="utf-8")
    return sorted(set(re.findall(r'output\s+"([^"]+)"', declarations)))


def _reading_files(output_name: str) -> list:
    """List the Terraform files that read one output off a module."""
    reference = re.compile(rf"module\.\w+\.{re.escape(output_name)}\b")
    return sorted(
        path
        for root in SEARCH_ROOTS
        for path in root.rglob("*.tf")
        if reference.search(path.read_text(encoding="utf-8"))
    )


@pytest.mark.parametrize("output_name", _declared_output_names())
def test_output_is_read_by_a_stack(output_name: str) -> None:
    """Test that some Terraform file reads this output off the module."""
    assert _reading_files(output_name), (
        f"the common module declares output {output_name} but no .tf file "
        f"under src/ or lib/ writes module.<name>.{output_name}, so nothing "
        f"consumes the value it publishes"
    )
