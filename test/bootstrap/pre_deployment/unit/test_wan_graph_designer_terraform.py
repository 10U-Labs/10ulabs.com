"""Unit tests for the deploy role declared in wan_graph_designer.tf.

The role carries AdministratorAccess over the whole AWS account, and its trust
policy hands that right to every GitHub repository whose name matches one of the
patterns it lists. A pattern naming a repository the organisation does not have
is an open offer: whoever creates a repository at that name gets administrator
rights on its first workflow run. Every pattern must therefore name a repository
that exists, or one the synthesizer is in the course of renaming itself to.
"""
import re

SUBJECT_CONDITION = re.compile(
    r'"token\.actions\.githubusercontent\.com:sub"\s*=\s*\[([^\]]*)\]'
)


def _trusted_repository_patterns(bootstrap_dir):
    """Read the repository patterns the trust policy lets assume the role."""
    with open(bootstrap_dir / "wan_graph_designer.tf", encoding='utf-8') as f:
        match = SUBJECT_CONDITION.search(f.read())
    return re.findall(r'"([^"]+)"', match.group(1)) if match else []


def test_trust_policy_names_only_the_synthesizer_under_both_its_names(bootstrap_dir):
    """Test that the repositories trusted are the synthesizer's old and new names.

    The repository is being renamed from wan-graph-synthesizer to wan-synthesizer, and
    GitHub puts its current name in the OIDC token's sub claim. Both are allowed across
    the rename so that a rename which has to be undone leaves the deploys working either
    way; the old name goes once the rename has held.
    """
    expected = [
        "repo:${local.github_org}/wan-graph-synthesizer:*",
        "repo:${local.github_org}/wan-synthesizer:*",
    ]
    assert _trusted_repository_patterns(bootstrap_dir) == expected
