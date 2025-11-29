from test.rack_designer import load_lambda_module
import pytest


@pytest.fixture(name="handler")
def handler_fixture():
    module = load_lambda_module("handler.py", "handler")
    module.clear_clients()
    return module
