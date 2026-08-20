"""Unit tests for the deploy role declared in wan_graph_designer.tf.

The role carries AdministratorAccess over the whole AWS account, and its trust
policy hands that right to every GitHub repository whose name matches one of the
patterns it lists. A pattern naming a repository the organisation does not have
is an open offer: whoever creates a repository at that name gets administrator
rights on its first workflow run. Every pattern must therefore name a repository
that exists.
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


def test_trust_policy_names_only_wan_graph_synthesizer(bootstrap_dir):
    """Test that the only repository trusted is wan-graph-synthesizer."""
    expected = ["repo:${local.github_org}/wan-graph-synthesizer:*"]
    assert _trusted_repository_patterns(bootstrap_dir) == expected
