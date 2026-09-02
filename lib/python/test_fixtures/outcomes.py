from typing import Any, Callable

import pytest


def accepted(check: Callable[..., None], *args: Any, **kwargs: Any) -> bool:
    try:
        check(*args, **kwargs)
    except (AssertionError, pytest.fail.Exception, pytest.skip.Exception):
        return False
    return True
