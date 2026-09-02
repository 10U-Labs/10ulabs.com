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


class TestAcceptedOutcome:
    def test_returns_true_when_the_check_returns(self) -> None:
        assert accepted(_returns) is True

    def test_returns_false_when_the_check_asserts(self) -> None:
        assert accepted(_asserts) is False

    def test_returns_false_when_the_check_fails(self) -> None:
        assert accepted(_fails) is False

    def test_returns_false_when_the_check_skips(self) -> None:
        assert accepted(_skips) is False

    def test_raises_what_the_check_raises_for_anything_else(self) -> None:
        with pytest.raises(ValueError):
            accepted(_raises_value_error)


class TestAcceptedArguments:
    def test_passes_positional_arguments_to_the_check(self) -> None:
        seen: list = []
        accepted(seen.append, "positional")
        assert seen == ["positional"]

    def test_passes_keyword_arguments_to_the_check(self) -> None:
        seen: dict = {}
        accepted(lambda **kwargs: seen.update(kwargs), keyword="value")
        assert seen == {"keyword": "value"}
