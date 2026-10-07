import re
from pathlib import Path
from typing import Callable

from repo_utils import REPO_ROOT


def _declared_state_key(backend_content: str) -> str:
    match = re.search(r'^\s*key\s*=\s*"([^"]+)"', backend_content, re.MULTILINE)
    return match.group(1) if match else "<backend.tf declares no key>"


def _declared_concurrency_group(workflow_content: str, workflow_name: str) -> str:
    match = re.search(r'^\s*group:\s*(\S+)', workflow_content, re.MULTILINE)
    return match.group(1) if match else f"<{workflow_name} declares no concurrency group>"


def create_state_lock_contract_tests(
    stack_src: Path,
    workflow_name: str
) -> Callable[[], None]:
    workflow_path = REPO_ROOT / ".github" / "workflows" / workflow_name

    def test_group_names_the_state_file() -> None:
        state_key = _declared_state_key((stack_src / "backend.tf").read_text())
        group = _declared_concurrency_group(workflow_path.read_text(), workflow_name)

        assert state_key == group, (
            f"backend.tf key '{state_key}' and {workflow_name} concurrency "
            f"group '{group}' differ. They are held equal as a naming "
            f"convention, so the lock is legible from either side and a "
            f"second workflow that writes this state file gets the right "
            f"lock by spelling its group the same way."
        )

    return test_group_names_the_state_file
