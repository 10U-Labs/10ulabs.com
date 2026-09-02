from hcl2 import SerializationOptions

from test_fixtures.hcl import V7_COMPATIBLE


def test_v7_compatible_is_a_serialization_options() -> None:
    assert isinstance(V7_COMPATIBLE, SerializationOptions)
