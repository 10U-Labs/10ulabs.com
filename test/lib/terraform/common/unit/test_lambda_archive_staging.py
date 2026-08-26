import re
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT
from terraform_config import packaged_lambda_archives

SRC_ROOT = REPO_ROOT / "src"
SCRATCH_DIRECTORY_NAME = ".terraform"


def _terraform_files() -> list:
    return sorted(
        path
        for path in SRC_ROOT.rglob("*.tf")
        if SCRATCH_DIRECTORY_NAME not in path.parts
    )


def _staged_archives() -> list:
    return sorted(
        (str(path.relative_to(REPO_ROOT)), archive)
        for path in _terraform_files()
        for archive in packaged_lambda_archives(path)
    )


def _files_declaring_a_package() -> list:
    declared: list = []
    for path in _terraform_files():
        content = path.read_text(encoding="utf-8")
        packages = len(re.findall(r'data\s+"archive_file"', content))
        if packages:
            declared.append((str(path.relative_to(REPO_ROOT)), packages))
    return sorted(declared)


@pytest.mark.parametrize("tf_file, archive", _staged_archives())
def test_packaged_function_is_staged_in_the_deployment_scratch_directory(
    tf_file: str, archive: str
) -> None:
    assert Path(archive).parts[:1] == (SCRATCH_DIRECTORY_NAME,), (
        f"{tf_file} writes its archive to {archive}, so a build output lands in a "
        f"directory holding source; every other deployed function is staged beneath "
        f"{SCRATCH_DIRECTORY_NAME}, which is where the deployment tool already keeps "
        f"its own working files"
    )


@pytest.mark.parametrize("tf_file, declared", _files_declaring_a_package())
def test_every_packaging_configuration_names_the_archive_it_writes(
    tf_file: str, declared: int
) -> None:
    read = len(packaged_lambda_archives(REPO_ROOT / tf_file))
    assert read == declared, (
        f"{tf_file} declares {declared} packages and {read} archive paths were read "
        f"from it, so a package is staged somewhere nothing checks; the check above "
        f"reads the paths it finds and cannot report on one it never saw"
    )
