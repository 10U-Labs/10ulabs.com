"""Comprehensive tests for test_utils package entry points."""
import sys

from test_utils import create_endpoint_handler_loader


ENDPOINT = "demo"


def _endpoint_lambda_dir(root):
    """Return the lambda directory the loader builds for ENDPOINT under root."""
    return root / "src" / "api" / "endpoints" / ENDPOINT / "lambda"


class TestCreateEndpointHandlerLoader:
    """Tests for create_endpoint_handler_loader function."""

    def test_inserts_lambda_directory_at_front_of_sys_path(
        self, tmp_path, monkeypatch
    ):
        """create_endpoint_handler_loader puts the lambda dir first on sys.path."""
        monkeypatch.setattr("test_utils.REPO_ROOT", tmp_path)
        monkeypatch.setattr(sys, "path", list(sys.path))
        create_endpoint_handler_loader(ENDPOINT)
        assert sys.path[0] == str(_endpoint_lambda_dir(tmp_path))

    def test_leaves_sys_path_unchanged_when_directory_present(
        self, tmp_path, monkeypatch
    ):
        """create_endpoint_handler_loader adds nothing when the dir is on sys.path."""
        monkeypatch.setattr("test_utils.REPO_ROOT", tmp_path)
        seeded = [str(_endpoint_lambda_dir(tmp_path))] + list(sys.path)
        monkeypatch.setattr(sys, "path", seeded)
        create_endpoint_handler_loader(ENDPOINT)
        assert sys.path == seeded

    def test_returns_loader_that_loads_from_lambda_directory(
        self, tmp_path, monkeypatch
    ):
        """create_endpoint_handler_loader returns a loader for the lambda dir."""
        lambda_dir = _endpoint_lambda_dir(tmp_path)
        lambda_dir.mkdir(parents=True)
        (lambda_dir / "widget.py").write_text("MARKER = 'loaded'\n")
        monkeypatch.setattr("test_utils.REPO_ROOT", tmp_path)
        monkeypatch.setattr(sys, "path", list(sys.path))
        loader = create_endpoint_handler_loader(ENDPOINT)
        assert loader("widget.py", "widget").MARKER == "loaded"
