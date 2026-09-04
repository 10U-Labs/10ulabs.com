import re
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT, extract_brace_block

MODULES_DIR = REPO_ROOT / "lib" / "terraform"
CALLER_ROOTS = (REPO_ROOT / "src", REPO_ROOT / "lib")
MODULE_BLOCK = re.compile(r'module\s+"[^"]+"\s*\{')
SOURCE_ATTRIBUTE = re.compile(r'source\s*=\s*"([^"]+)"')


MODULE_NAMES = ["common", "s3_bucket"]


def _sourced_directories(caller: Path) -> set:
    declarations = caller.read_text(encoding="utf-8")
    blocks = (
        extract_brace_block(declarations, opening.end() - 1)
        for opening in MODULE_BLOCK.finditer(declarations)
    )
    sources = (SOURCE_ATTRIBUTE.search(block) for block in blocks)
    return {
        (caller.parent / source.group(1)).resolve()
        for source in sources
        if source is not None
    }


def _instantiating_files(module_name: str) -> list:
    module_dir = (MODULES_DIR / module_name).resolve()
    return sorted(
        caller
        for root in CALLER_ROOTS
        for caller in root.rglob("*.tf")
        if module_dir in _sourced_directories(caller)
    )


@pytest.mark.parametrize("module_name", MODULE_NAMES)
def test_module_is_instantiated_by_a_stack(module_name: str) -> None:
    assert _instantiating_files(module_name), (
        f"lib/terraform/{module_name} declares a module but no .tf file under "
        f"src/ or lib/ has a module block whose source resolves to it, so "
        f"nothing ever plans or applies what it declares"
    )
