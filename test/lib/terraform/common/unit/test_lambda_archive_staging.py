"""Tests that every deployed function is staged in the deployment tool's scratch.

A deployed function is packaged into an archive before it is uploaded, and that
archive is a build output: it is produced from the source on every run, it is
never edited, and nothing outside the deployment reads it. Version control
ignores archives by extension rather than by location, so one written into the
directory holding the source it packages is as invisible as one written into the
scratch directory the deployment tool already keeps its own working files in. The
only way to tell the two apart was to run the deployment and look at what
appeared, which is how a source directory came to hold a build output for as long
as it did.

The cost is that a source directory stops being only source. Anyone reading it to
see what gets deployed finds a file that is not part of the answer, and any tool
pointed at the directory has to be given a rule for skipping it.

The second test here is what keeps the first honest. The first reads the archive
paths out of the packaging configurations it finds, so a configuration whose path
it fails to read is a configuration it silently stops checking; the second holds
the count it read against the number of packaging configurations there are.
"""
import re
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT
from terraform_config import packaged_lambda_archives

SRC_ROOT = REPO_ROOT / "src"
SCRATCH_DIRECTORY_NAME = ".terraform"


def _terraform_files() -> list:
    """List the Terraform files under the source tree."""
    return sorted(
        path
        for path in SRC_ROOT.rglob("*.tf")
        if SCRATCH_DIRECTORY_NAME not in path.parts
    )


def _staged_archives() -> list:
    """List the archive each packaging configuration under src/ writes."""
    return sorted(
        (str(path.relative_to(REPO_ROOT)), archive)
        for path in _terraform_files()
        for archive in packaged_lambda_archives(path)
    )


def _files_declaring_a_package() -> list:
    """List each Terraform file that packages anything, with how many it packages."""
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
    """Test that this packaging configuration stages its archive out of the source."""
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
    """Test that every packaging configuration in this file is read as an archive."""
    read = len(packaged_lambda_archives(REPO_ROOT / tf_file))
    assert read == declared, (
        f"{tf_file} declares {declared} packages and {read} archive paths were read "
        f"from it, so a package is staged somewhere nothing checks; the check above "
        f"reads the paths it finds and cannot report on one it never saw"
    )
