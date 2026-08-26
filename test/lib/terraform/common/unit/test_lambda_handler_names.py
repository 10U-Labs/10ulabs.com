import pytest

from repo_utils import REPO_ROOT
from terraform_config import parse_lambda_handler_names

SRC_ROOT = REPO_ROOT / "src"


def _referencing_files(handler_key: str) -> list:
    reference = f"lambda_handler_names.{handler_key}"
    return sorted(
        path for path in SRC_ROOT.rglob("*.tf")
        if reference in path.read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("handler_key", sorted(parse_lambda_handler_names()))
def test_handler_name_is_read_by_a_stack(handler_key: str) -> None:
    assert _referencing_files(handler_key), (
        f"lambda_handler_names.{handler_key} is declared by the common module "
        f"but read by no .tf file under src/, so no stack creates the function "
        f"it names"
    )
