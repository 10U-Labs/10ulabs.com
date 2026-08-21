"""Contract tests between invalidate_cloudfront.py and the workflows.

Four deploys run the script as the last thing they do before their
post-deployment tests. The script exits non-zero on a missing required
argument, so a renamed flag breaks those deploys and nothing else reads
both sides to notice.
"""
import ast
import re

from repo_utils import REPO_ROOT


SCRIPT = REPO_ROOT / "scripts" / "invalidate_cloudfront.py"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
STEP_BOUNDARY = re.compile(r"\n {6}- ")


def _required_arguments():
    """Return the flags invalidate_cloudfront.py declares as required."""
    tree = ast.parse(SCRIPT.read_text())
    return [
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        and any(
            keyword.arg == "required" and keyword.value.value is True
            for keyword in node.keywords
        )
    ]


def _invoking_steps():
    """Return every workflow step whose run block calls the script."""
    return [
        (path.name, step)
        for path in sorted(WORKFLOWS.glob("*.yml"))
        for step in STEP_BOUNDARY.split(path.read_text())
        if "scripts/invalidate_cloudfront.py" in step
    ]


class TestInvalidateCloudfrontInvocations:
    """Verify every caller passes the arguments the script requires."""

    def test_every_invocation_passes_every_required_argument(self):
        """Each step calling the script passes all of its required flags."""
        required = _required_arguments()
        missing = [
            f"{name}:{flag}"
            for name, step in _invoking_steps()
            for flag in required
            if flag not in step
        ]
        assert missing == []
