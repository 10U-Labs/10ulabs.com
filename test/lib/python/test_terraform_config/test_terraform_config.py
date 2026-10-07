from terraform_config import TEST_AWS_REGION


def test_is_string() -> None:
    assert isinstance(TEST_AWS_REGION, str)


def test_is_valid_region_format() -> None:
    assert TEST_AWS_REGION.startswith("us-") or TEST_AWS_REGION.startswith("eu-")
