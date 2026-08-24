"""Tests that every deployed function is one handler file beneath one directory.

A deployed function is a single Python file that the packaging step copies into
an archive and the runtime enters. Nothing about the tree decides what that file
is called or where it sits, because the runtime is told which module to enter and
any name works as long as the two agree. Left to itself the layout drifted: some
files were named for the job they do and some were not, the directory holding them
was spelled two ways, and one subsystem carried both spellings side by side with
one file in each. Every one of those differences turned out to mean nothing, and
the cost of a difference that means nothing is paid by whoever reads it next and
has to establish that.

The third test here holds the part of the layout that does mean something. One
file name across every function is safe only while each function has a directory
to itself, because two modules of one name in a single subsystem are resolvable by
import order rather than by which one was asked for, and a type checker refuses a
run in which two files claim the same module name.
"""
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT
from terraform_config import packaged_lambda_sources

SRC_ROOT = REPO_ROOT / "src"
HANDLER_FILE_NAME = "handler.py"
LAMBDA_DIRECTORY_NAME = "lambda"


def _packaged_functions() -> list:
    """List the function file each packaging configuration under src/ packages."""
    return sorted(
        (str(path.relative_to(REPO_ROOT)), packaged)
        for path in SRC_ROOT.rglob("*.tf")
        if ".terraform" not in path.parts
        for packaged in packaged_lambda_sources(path)
    )


def _stacks_with_their_packaging_directories() -> list:
    """List the directories each stack packages its functions from."""
    stacks: dict = {}
    for tf_file, packaged in _packaged_functions():
        stacks.setdefault(str(Path(tf_file).parent), []).append(
            str(Path(packaged).parent)
        )
    return sorted(stacks.items())


@pytest.mark.parametrize("tf_file, packaged", _packaged_functions())
def test_packaged_function_carries_the_agreed_file_name(
    tf_file: str, packaged: str
) -> None:
    """Test that this packaging configuration packages the agreed file name."""
    assert Path(packaged).name == HANDLER_FILE_NAME, (
        f"{tf_file} packages {packaged}, so this function is named for the job "
        f"it does while every other deployed function is named {HANDLER_FILE_NAME}; "
        f"the directory above it and the deployed function's own name already say "
        f"what it does"
    )


@pytest.mark.parametrize("tf_file, packaged", _packaged_functions())
def test_packaged_function_sits_beneath_the_agreed_directory(
    tf_file: str, packaged: str
) -> None:
    """Test that this packaging configuration packages from the agreed directory."""
    assert Path(packaged).parent.parts[:1] == (LAMBDA_DIRECTORY_NAME,), (
        f"{tf_file} packages {packaged}, which is not beneath a directory called "
        f"{LAMBDA_DIRECTORY_NAME}; every deployed function in every other subsystem "
        f"is, and the plural spelling marks nothing because no such directory holds "
        f"more than one function"
    )


@pytest.mark.parametrize("stack, directories", _stacks_with_their_packaging_directories())
def test_each_function_in_a_stack_is_packaged_from_its_own_directory(
    stack: str, directories: list
) -> None:
    """Test that no two functions in this stack are packaged from one directory."""
    assert len(set(directories)) == len(directories), (
        f"{stack} packages more than one function from {directories}, so two "
        f"modules of one name share a subsystem; give each function a directory "
        f"named for what it does, because the shared file name is only safe while "
        f"nothing else claims it"
    )
