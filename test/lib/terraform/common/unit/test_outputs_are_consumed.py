import re

import pytest

from repo_utils import REPO_ROOT

SEARCH_ROOTS = (REPO_ROOT / "src", REPO_ROOT / "lib")
OUTPUTS_PATH = REPO_ROOT / "lib" / "terraform" / "common" / "outputs.tf"


def _declared_output_names() -> list:
    declarations = OUTPUTS_PATH.read_text(encoding="utf-8")
    return sorted(set(re.findall(r'output\s+"([^"]+)"', declarations)))


def _reading_files(output_name: str) -> list:
    reference = re.compile(rf"module\.\w+\.{re.escape(output_name)}\b")
    return sorted(
        path
        for root in SEARCH_ROOTS
        for path in root.rglob("*.tf")
        if reference.search(path.read_text(encoding="utf-8"))
    )


@pytest.mark.parametrize("output_name", _declared_output_names())
def test_output_is_read_by_a_stack(output_name: str) -> None:
    assert _reading_files(output_name), (
        f"the common module declares output {output_name} but no .tf file "
        f"under src/ or lib/ writes module.<name>.{output_name}, so nothing "
        f"consumes the value it publishes"
    )
