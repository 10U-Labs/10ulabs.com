"""Unit tests for the deploy roles the WAN synthesizer assumes.

The role carries AdministratorAccess over the whole AWS account, and its trust
policy hands that right to every GitHub repository whose name matches one of the
patterns it lists. A pattern naming a repository the organisation does not have
is an open offer: whoever creates a repository at that name gets administrator
rights on its first workflow run. Every pattern must therefore name a repository
that exists, or one the synthesizer is in the course of renaming itself to.
"""
import re

import pytest

# The role is being renamed from TenULabsWanGraphDesignerRole to
# TenULabsWanSynthesizerRole. Both exist while the repository's OIDC_ROLE_ARN is moved
# from one to the other, and both trust exactly the same repository, so both are asserted
# here until the old one is destroyed.
ROLE_FILES = ("wan_graph_designer.tf", "wan_synthesizer.tf")

SUBJECT_CONDITION = re.compile(
    r'"token\.actions\.githubusercontent\.com:sub"\s*=\s*\[([^\]]*)\]'
)


def _trusted_repository_patterns(bootstrap_dir, role_file):
    """Read the repository patterns the trust policy lets assume the role.

    Comment lines inside the list are dropped before the patterns are read off it. A
    comment is free to quote a command or a name, and a quoted word in one is not a
    repository the role trusts.
    """
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
def test_trust_policy_names_only_the_synthesizer(bootstrap_dir, role_file):
    """Test that the only repository trusted is wan-synthesizer, by both its subjects.

    GitHub puts the repository's name in the OIDC token's sub claim, and after a rename it
    qualifies that name with the organisation's id and the repository's. The qualified
    form is the one tokens match; the plain one is kept because it is what GitHub would
    issue if the qualification were ever lifted, and it names the same repository.
    """
    expected = [
        "repo:${local.github_org}/wan-synthesizer:*",
        "repo:${local.github_org}@240548037/wan-synthesizer@1262350676:*",
    ]
    assert _trusted_repository_patterns(bootstrap_dir, role_file) == expected
