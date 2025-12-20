"""Path setup for all tests.

This conftest.py sets up lib/python in sys.path so tests can import
modules like repo_utils, terraform_config, and test_fixtures.

AWS fixtures are in lib/python/test_fixtures/aws.py. Test directories
that need them should declare: pytest_plugins = ['test_fixtures.aws']
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_LIB_DIR = _REPO_ROOT / "lib" / "python"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))
