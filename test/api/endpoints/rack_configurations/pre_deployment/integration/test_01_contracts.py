import re
import subprocess
from pathlib import Path
from typing import List

from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import (
    create_lambda_source_contract_tests,
    create_state_lock_contract_tests,
)


RACK_CONFIGURATIONS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "rack_configurations"


TestLambdaSourceContract = create_lambda_source_contract_tests(
    endpoint_src=RACK_CONFIGURATIONS_SRC,
    tf_file="lambda.tf",
    resource_name="handler",
)

test_group_names_the_state_file = create_state_lock_contract_tests(
    RACK_CONFIGURATIONS_SRC, "api_endpoint_v1_rack_configurations.yml"
)


RESOURCE_PREFIX_LITERAL = re.compile(
    r'"[^"\n]*\$\{\s*(?:local|module\.common)\.resource_prefix\s*\}[^"\n]*"'
)


def _tracked_tf_files_outside_locals() -> List[Path]:
    listing = subprocess.run(
        ["git", "ls-files", "*.tf"],
        cwd=RACK_CONFIGURATIONS_SRC,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [
        RACK_CONFIGURATIONS_SRC / name for name in listing if name != "locals.tf"
    ]


def _find_resource_prefix_literals_outside_locals_tf() -> List[str]:
    offences: List[str] = []
    for tf_path in _tracked_tf_files_outside_locals():
        lines = tf_path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, start=1):
            for literal in RESOURCE_PREFIX_LITERAL.findall(line):
                offences.append(
                    f"{tf_path.relative_to(REPO_ROOT)}:{line_number}: {literal}"
                )
    return offences


def _get_shared_tf_content() -> str:
    shared_tf_path = RACK_CONFIGURATIONS_SRC / "shared.tf"
    with open(shared_tf_path, encoding="utf-8") as f:
        return f.read()


def test_shared_tf_module_source_path_exists() -> None:
    content = _get_shared_tf_content()
    source_match = re.search(r'source\s*=\s*"([^"]+)"', content)
    source_path = source_match.group(1) if source_match else "(no module source declared)"
    resolved_path = (RACK_CONFIGURATIONS_SRC / source_path).resolve()
    assert resolved_path.exists(), (
        f"Module source path does not exist: {source_path}"
    )


def test_only_locals_tf_builds_names_from_the_resource_prefix() -> None:
    offences = _find_resource_prefix_literals_outside_locals_tf()

    assert not offences, (
        "Terraform files other than locals.tf build a resource name from "
        "the module's resource prefix. locals.tf exists to hold those "
        "names once, so that renaming one is a single edit and so that "
        "get_endpoint_local_values() can read it. Move each of these into "
        "a local and reference it:\n" + "\n".join(offences)
    )
