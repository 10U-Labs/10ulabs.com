import pytest
from hcl2 import SerializationOptions


@pytest.fixture(scope="session")
def v7_compatible():
    return SerializationOptions(
        strip_string_quotes=True,
        explicit_blocks=False,
        with_comments=False,
        preserve_heredocs=False,
    )
