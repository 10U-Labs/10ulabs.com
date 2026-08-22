"""Contract tests over the test_utils package source.

An assertion helper that skips instead of failing reports a green run
exactly when the resource it checks for is missing, so no helper in this
package may call pytest.skip.
"""
import ast

from repo_utils import REPO_ROOT


TEST_UTILS_SRC = REPO_ROOT / "lib" / "python" / "test_utils"


def _is_pytest_skip(node):
    """Report whether node is a call to pytest.skip."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute):
        return (
            func.attr == "skip"
            and isinstance(func.value, ast.Name)
            and func.value.id == "pytest"
        )
    return isinstance(func, ast.Name) and func.id == "skip"


def _skip_callers(path):
    """Name every function in path whose body calls pytest.skip."""
    tree = ast.parse(path.read_text())
    return [
        f"{path.name}:{node.name}"
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        for call in ast.walk(node)
        if _is_pytest_skip(call)
    ]


def test_no_assertion_helper_skips():
    """No function under lib/python/test_utils/ calls pytest.skip."""
    callers = [
        name
        for path in sorted(TEST_UTILS_SRC.glob("*.py"))
        for name in _skip_callers(path)
    ]
    assert callers == [], (
        f"assertion helpers must fail rather than skip: {callers}"
    )
