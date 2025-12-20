"""Pytest configuration for workflowctl tests."""

import sys

from repo_utils import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src" / "workflowctl"))
