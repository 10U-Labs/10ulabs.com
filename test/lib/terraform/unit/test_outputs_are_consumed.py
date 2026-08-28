import re

import pytest

from repo_utils import REPO_ROOT

SEARCH_ROOTS = (REPO_ROOT / "src", REPO_ROOT / "lib")
MODULES_DIR = REPO_ROOT / "lib" / "terraform"


def _declared_output_pairs() -> list:
    return sorted(
        (outputs.parent.name, output_name)
        for outputs in MODULES_DIR.glob("*/outputs.tf")
        for output_name in set(
            re.findall(r'output\s+"([^"]+)"', outputs.read_text(encoding="utf-8"))
        )
    )


def _reading_files(output_name: str) -> list:
    reference = re.compile(rf"module\.\w+\.{re.escape(output_name)}\b")
    return sorted(
        path
        for root in SEARCH_ROOTS
        for path in root.rglob("*.tf")
        if reference.search(path.read_text(encoding="utf-8"))
    )


@pytest.mark.parametrize("module_name,output_name", _declared_output_pairs())
def test_output_is_read_by_a_stack(module_name: str, output_name: str) -> None:
    assert _reading_files(output_name), (
        f"lib/terraform/{module_name} declares output {output_name} but no .tf "
        f"file under src/ or lib/ writes module.<name>.{output_name}, so "
        f"nothing consumes the value it publishes"
    )
