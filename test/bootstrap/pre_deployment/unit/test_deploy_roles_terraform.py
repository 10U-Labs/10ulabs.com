import re
from pathlib import Path
from typing import List

import pytest

ROLE_FILES = ("wan_synthesizer.tf",)

SUBJECT_CONDITION = re.compile(
    r'"token\.actions\.githubusercontent\.com:sub"\s*=\s*\[([^\]]*)\]'
)


def _trusted_repository_patterns(bootstrap_dir: Path, role_file: str) -> List[str]:
    with open(bootstrap_dir / role_file, encoding='utf-8') as f:
        match = SUBJECT_CONDITION.search(f.read())
    if match is None:
        return []
    entries = [
        line for line in match.group(1).splitlines()
        if not line.lstrip().startswith("#")
    ]
    return re.findall(r'"([^"]+)"', "\n".join(entries))


@pytest.mark.parametrize("role_file", ROLE_FILES)
def test_trust_policy_names_only_the_synthesizer(bootstrap_dir: Path, role_file: str) -> None:
    expected = [
        "repo:${local.github_org}/wan-synthesizer:*",
        "repo:${local.github_org}@240548037/wan-synthesizer@1262350676:*",
    ]
    assert _trusted_repository_patterns(bootstrap_dir, role_file) == expected
