import sys
from pathlib import Path
import pytest

src_path = Path(__file__).parent.parent.parent.parent / "src" / "rack_designer" / "lambdas"
sys.path.insert(0, str(src_path))


@pytest.fixture(name="handler")
def handler_fixture():
    import handler
    handler._dynamodb_client = None
    return handler
