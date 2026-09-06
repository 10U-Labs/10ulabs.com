import pytest

from test_fixtures.outcomes import accepted


def _returns() -> None:
    pass


def _asserts() -> None:
    raise AssertionError("rejected")


def _fails() -> None:
    pytest.fail("rejected")


def _skips() -> None:
    pytest.skip("not deployed")


def _raises_value_error() -> None:
    raise ValueError("something else")


def test_returns_true_when_the_check_returns() -> None:
    assert accepted(_returns) is True


def test_returns_false_when_the_check_asserts() -> None:
    assert accepted(_asserts) is False


def test_returns_false_when_the_check_fails() -> None:
    assert accepted(_fails) is False


def test_returns_false_when_the_check_skips() -> None:
    assert accepted(_skips) is False


def test_raises_what_the_check_raises_for_anything_else() -> None:
    with pytest.raises(ValueError):
        accepted(_raises_value_error)


def test_passes_positional_arguments_to_the_check() -> None:
    seen: list = []
    accepted(seen.append, "positional")
    assert seen == ["positional"]


def test_passes_keyword_arguments_to_the_check() -> None:
    seen: dict = {}
    accepted(lambda **kwargs: seen.update(kwargs), keyword="value")
    assert seen == {"keyword": "value"}
